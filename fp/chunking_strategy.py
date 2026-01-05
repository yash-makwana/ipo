# chunking_strategy.py
# Specialized chunking for Graph RAG retrieval

import re
from typing import List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class Chunk:
    """Represents a text chunk with metadata for RAG"""
    chunk_id: str
    text: str
    chunk_type: str  # 'requirement', 'section_full', 'context'
    metadata: Dict
    token_count: int
    embeddings: List[float] = None

class LegalDocumentChunker:
    """
    Chunking strategy optimized for legal documents and Graph RAG
    """
    
    def __init__(self, max_chunk_size=512, overlap=50):
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
    
    def chunk_section(self, section_data: Dict, chapter_metadata: Dict) -> List[Chunk]:
        """
        Create multiple chunks from a single section for better retrieval
        
        Strategy:
        1. Individual compliance requirements (highest priority)
        2. Full section text (for context)
        3. Overlapping windows (for continuity)
        """
        chunks = []
        
        base_metadata = {
            'regulation_id': chapter_metadata['regulation_id'],
            'regulation_name': chapter_metadata['regulation_name'],
            'chapter_number': chapter_metadata['chapter_number'],
            'chapter_title': chapter_metadata['chapter_title'],
            'section_number': section_data['number'],
            'section_title': section_data['title']
        }
        
        # Strategy 1: Compliance Requirements (Most Important)
        for idx, compliance_item in enumerate(section_data.get('compliance_items', [])):
            chunk_text = self._format_compliance_chunk(
                section_data,
                compliance_item,
                chapter_metadata
            )
            
            chunks.append(Chunk(
                chunk_id=f"{section_data['number']}_req_{idx}",
                text=chunk_text,
                chunk_type='requirement',
                metadata={
                    **base_metadata,
                    'compliance_category': compliance_item.get('category'),
                    'is_mandatory': compliance_item.get('mandatory'),
                    'deadline_type': compliance_item.get('deadline_type'),
                    'applies_to': compliance_item.get('applies_to', [])
                },
                token_count=len(chunk_text.split())
            ))
        
        # Strategy 2: Full Section (for comprehensive context)
        full_text = section_data.get('full_text', '')
        if full_text and len(full_text) > 200:
            section_chunk = self._format_section_chunk(
                section_data,
                chapter_metadata
            )
            
            chunks.append(Chunk(
                chunk_id=f"{section_data['number']}_full",
                text=section_chunk,
                chunk_type='section_full',
                metadata={
                    **base_metadata,
                    'has_compliance_items': len(section_data.get('compliance_items', [])) > 0
                },
                token_count=len(section_chunk.split())
            ))
        
        # Strategy 3: Sliding window for very long sections
        if len(full_text.split()) > self.max_chunk_size:
            window_chunks = self._create_sliding_windows(
                full_text,
                section_data,
                base_metadata
            )
            chunks.extend(window_chunks)
        
        return chunks
    
    def _format_compliance_chunk(self, section_data: Dict, compliance_item: Dict, 
                                  chapter_metadata: Dict) -> str:
        """
        Format compliance requirement with context for better RAG retrieval
        """
        return f"""REGULATION: {chapter_metadata['regulation_name']}
CHAPTER: {chapter_metadata['chapter_number']} - {chapter_metadata['chapter_title']}
SECTION: {section_data['number']} - {section_data['title']}

REQUIREMENT:
{compliance_item['requirement_text']}

MANDATORY: {'Yes' if compliance_item.get('mandatory') else 'No'}
CATEGORY: {compliance_item.get('category', 'General')}
DEADLINE: {compliance_item.get('deadline_type', 'Not specified')}
APPLIES TO: {', '.join(compliance_item.get('applies_to', ['All']))}

CONTEXT:
{section_data.get('summary', section_data.get('full_text', '')[:300])}"""
    
    def _format_section_chunk(self, section_data: Dict, chapter_metadata: Dict) -> str:
        """
        Format full section with hierarchical context
        """
        return f"""REGULATION: {chapter_metadata['regulation_name']}
CHAPTER: {chapter_metadata['chapter_number']} - {chapter_metadata['chapter_title']}
SECTION: {section_data['number']} - {section_data['title']}

FULL TEXT:
{section_data.get('full_text', '')}

SUMMARY:
{section_data.get('summary', 'No summary available')}"""
    
    def _create_sliding_windows(self, full_text: str, section_data: Dict, 
                                base_metadata: Dict) -> List[Chunk]:
        """
        Create overlapping chunks for very long sections
        """
        words = full_text.split()
        chunks = []
        
        for i in range(0, len(words), self.max_chunk_size - self.overlap):
            window = words[i:i + self.max_chunk_size]
            window_text = ' '.join(window)
            
            chunks.append(Chunk(
                chunk_id=f"{section_data['number']}_window_{i}",
                text=f"Section {section_data['number']}: {section_data['title']}\n\n{window_text}",
                chunk_type='context',
                metadata={
                    **base_metadata,
                    'window_start': i,
                    'window_end': i + len(window)
                },
                token_count=len(window)
            ))
        
        return chunks

# ============================================================================
# INTEGRATION WITH NEO4J
# ============================================================================

def ingest_chunks_to_neo4j(chunks: List[Chunk], conn):
    """
    Store chunks in Neo4j alongside the main graph structure
    
    This creates a parallel structure optimized for RAG retrieval:
    (:Section)-[:HAS_CHUNK]->(:TextChunk)
    """
    print(f"💾 Ingesting {len(chunks)} chunks to Neo4j...")
    
    for chunk in chunks:
        # Create Chunk node
        conn.query("""
            MERGE (chunk:TextChunk {id: $chunk_id})
            SET chunk.text = $text,
                chunk.chunk_type = $chunk_type,
                chunk.token_count = $token_count,
                chunk.metadata = $metadata
            WITH chunk
            MATCH (s:Section {number: $section_number})
            MERGE (s)-[:HAS_CHUNK]->(chunk)
        """, {
            'chunk_id': chunk.chunk_id,
            'text': chunk.text,
            'chunk_type': chunk.chunk_type,
            'token_count': chunk.token_count,
            'metadata': chunk.metadata,
            'section_number': chunk.metadata['section_number']
        })
    
    print(f"   ✅ {len(chunks)} chunks ingested")

# ============================================================================
# USAGE EXAMPLE
# ============================================================================

def chunk_and_ingest_document(structured_data: Dict, conn):
    """
    Process entire document into chunks and ingest
    """
    chunker = LegalDocumentChunker(max_chunk_size=512, overlap=50)
    all_chunks = []
    
    for chapter_data in structured_data.get('chapters', []):
        chapter_metadata = {
            'regulation_id': structured_data['regulation_id'],
            'regulation_name': structured_data['regulation_name'],
            'chapter_number': chapter_data['number'],
            'chapter_title': chapter_data['title']
        }
        
        for section_data in chapter_data.get('sections', []):
            section_chunks = chunker.chunk_section(section_data, chapter_metadata)
            all_chunks.extend(section_chunks)
    
    print(f"\n📊 Created {len(all_chunks)} chunks from document")
    print(f"   - Requirement chunks: {sum(1 for c in all_chunks if c.chunk_type == 'requirement')}")
    print(f"   - Full section chunks: {sum(1 for c in all_chunks if c.chunk_type == 'section_full')}")
    print(f"   - Context chunks: {sum(1 for c in all_chunks if c.chunk_type == 'context')}")
    
    # Ingest to Neo4j
    ingest_chunks_to_neo4j(all_chunks, conn)
    
    return all_chunks

# ============================================================================
# RAG RETRIEVAL UTILITIES
# ============================================================================

def retrieve_relevant_chunks(query: str, conn, top_k: int = 5) -> List[Dict]:
    """
    Retrieve most relevant chunks for a query using Neo4j full-text search
    
    This would typically be combined with vector similarity search
    """
    # Use Neo4j full-text index
    results = conn.query("""
        CALL db.index.fulltext.queryNodes('section_text', $query)
        YIELD node, score
        MATCH (node)<-[:HAS_CHUNK]-(s:Section)<-[:HAS_SECTION]-(c:Chapter)<-[:HAS_CHAPTER]-(r:Regulation)
        RETURN node.text as chunk_text,
               node.chunk_type as chunk_type,
               node.metadata as metadata,
               s.number as section_number,
               s.title as section_title,
               c.title as chapter_title,
               r.name as regulation_name,
               score
        ORDER BY score DESC
        LIMIT $top_k
    """, {
        'query': query,
        'top_k': top_k
    })
    
    return results

if __name__ == "__main__":
    """
    Example usage
    """
    from db_config import get_neo4j_connection
    
    # Assuming you have structured_data from the ingestion pipeline
    # conn = get_neo4j_connection()
    # chunks = chunk_and_ingest_document(structured_data, conn)
    
    print("✅ Chunking strategy module ready")
    print("\nUsage:")
    print("1. After ingesting with ingest_legal_data_improved.py")
    print("2. Call chunk_and_ingest_document() to create chunks")
    print("3. Use retrieve_relevant_chunks() for RAG queries")