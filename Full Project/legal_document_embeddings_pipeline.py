"""
Legal Document Embeddings Pipeline - COMPLETE FIX
=================================================
Fixes:
1. Proper PDF structure detection for actual SEBI & Companies Act PDFs
2. Neo4j constraint handling (MERGE instead of CREATE)
3. Fallback chunking when structure detection fails
4. Better error handling
"""

from google.cloud import storage, aiplatform
from vertexai.language_models import TextEmbeddingModel
from neo4j import GraphDatabase
import PyPDF2
from io import BytesIO
import re
import os
import json
import uuid
from typing import List, Dict, Any
from dotenv import load_dotenv
import time

load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ID = os.environ.get('GCP_PROJECT')
NEO4J_URI = os.environ.get('NEO4J_URI')
NEO4J_USER = os.environ.get('NEO4J_USER')
NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD')

BUCKET_NAME = "ipo-compliance-system-legal-docs"
LEGAL_DOCS_FOLDER = "legal-docs"

DOCUMENTS = {
    "ICDR": {
        "filename": "ICDR_Regulations_2018.pdf",
        "regulation_name": "SEBI (Issue of Capital and Disclosure Requirements) Regulations, 2018",
        "short_name": "ICDR",
        "type": "SEBI_Regulation"
    },
    "COMPANIES_ACT": {
        "filename": "Companies_Act_2013.pdf",
        "regulation_name": "Companies Act, 2013",
        "short_name": "Companies Act",
        "type": "Act"
    }
}


# ============================================================================
# EMBEDDINGS SERVICE
# ============================================================================

class EmbeddingsGenerator:
    """Generate embeddings using Vertex AI"""
    
    def __init__(self):
        aiplatform.init(project=PROJECT_ID, location="us-central1")
        self.model = TextEmbeddingModel.from_pretrained("text-embedding-004")
        print("✅ Embeddings model initialized")
    
    def generate_embeddings(self, texts: List[str], batch_size: int = 5) -> List[List[float]]:
        """Generate embeddings in batches"""
        if not texts:
            return []
            
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            try:
                embeddings = self.model.get_embeddings(batch)
                for embedding in embeddings:
                    all_embeddings.append(embedding.values)
                
                if (i + batch_size) % 20 == 0:
                    print(f"   Generated embeddings for {min(i + batch_size, len(texts))}/{len(texts)} texts")
                
                time.sleep(0.5)
                    
            except Exception as e:
                print(f"   ⚠️  Error generating embeddings for batch {i}: {str(e)}")
                for _ in batch:
                    all_embeddings.append([0.0] * 768)
        
        return all_embeddings


# ============================================================================
# PDF EXTRACTION
# ============================================================================

class LegalDocumentExtractor:
    """Extract structured content from legal PDFs"""
    
    def __init__(self):
        self.storage_client = storage.Client()
    
    def extract_pdf_from_gcs(self, gcs_uri: str) -> Dict[str, Any]:
        """Extract full text from PDF in GCS"""
        print(f"\n📄 Extracting PDF: {gcs_uri}")
        
        try:
            bucket_name = gcs_uri.replace('gs://', '').split('/')[0]
            blob_path = '/'.join(gcs_uri.replace('gs://', '').split('/')[1:])
            
            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_path)
            pdf_bytes = blob.download_as_bytes()
            
            pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_bytes))
            
            pages = []
            full_text = ""
            
            print(f"   Pages: {len(pdf_reader.pages)}")
            
            for page_num, page in enumerate(pdf_reader.pages):
                text = page.extract_text()
                
                if text and len(text.strip()) > 50:
                    pages.append({
                        'page_number': page_num + 1,
                        'text': text
                    })
                    full_text += text + "\n\n"
            
            print(f"   ✅ Extracted {len(pages)} pages")
            
            return {
                'pages': pages,
                'full_text': full_text,
                'total_pages': len(pdf_reader.pages)
            }
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            raise


# ============================================================================
# IMPROVED CHUNKING - WORKS WITH ACTUAL PDF FORMAT
# ============================================================================

class LegalDocumentChunker:
    """Create meaningful chunks from legal documents"""
    
    def __init__(self, doc_type: str):
        self.doc_type = doc_type
    
    def detect_structure(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect document structure - IMPROVED for actual PDF format
        """
        print(f"\n🔍 Detecting {self.doc_type} structure...")
        
        if self.doc_type == "ICDR":
            chunks = self._extract_icdr_structure(text)
        else:
            chunks = self._extract_companies_act_structure(text)
        
        # Fallback if structure detection fails
        if len(chunks) == 0:
            print(f"   ⚠️  No structure detected, using fallback chunking...")
            chunks = self._fallback_chunking(text, self.doc_type)
        
        print(f"   ✅ Found {len(chunks)} structural chunks")
        return chunks
    
    def _extract_icdr_structure(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract ICDR structure - FIXED for actual SEBI PDF format
        
        Format: 
        CHAPTER I - PRELIMINARY
        Short title and commencement
        1. (1) These regulations...
        """
        chunks = []
        
        # Pattern for CHAPTER markers (from actual PDF)
        chapter_pattern = r'CHAPTER\s+([IVX]+)\s*[-–—]\s*([A-Z\s]+?)(?=\n|$)'
        chapter_matches = list(re.finditer(chapter_pattern, text))
        
        print(f"   Found {len(chapter_matches)} chapters")
        
        if len(chapter_matches) == 0:
            return []
        
        for i, chapter_match in enumerate(chapter_matches):
            chapter_num = chapter_match.group(1).strip()
            chapter_title = chapter_match.group(2).strip()
            
            # Get chapter content
            start_pos = chapter_match.end()
            end_pos = chapter_matches[i + 1].start() if i + 1 < len(chapter_matches) else len(text)
            chapter_text = text[start_pos:end_pos]
            
            # Find numbered regulations: "1.", "2.", etc.
            reg_pattern = r'\n\s*(\d+)\.\s+([^\n]{10,200})'
            reg_matches = list(re.finditer(reg_pattern, chapter_text))
            
            if len(reg_matches) > 0:
                # Extract individual regulations
                for j, reg_match in enumerate(reg_matches[:100]):  # Limit to 100 per chapter
                    reg_num = reg_match.group(1)
                    reg_title = reg_match.group(2).strip()[:200]
                    
                    reg_start = reg_match.start()
                    reg_end = reg_matches[j + 1].start() if j + 1 < len(reg_matches) else len(chapter_text)
                    reg_text = chapter_text[reg_start:reg_end].strip()[:5000]
                    
                    if len(reg_text) > 100:  # Only include substantial content
                        chunks.append({
                            'type': 'regulation',
                            'chapter_number': chapter_num,
                            'chapter_title': chapter_title,
                            'regulation_number': reg_num,
                            'regulation_title': reg_title,
                            'text': reg_text,
                            'chunk_id': f"ICDR_CH{chapter_num}_REG{reg_num}"
                        })
            else:
                # No regulations - chunk the whole chapter
                chunks.extend(self._chunk_large_text(
                    chapter_text,
                    prefix=f"ICDR_CH{chapter_num}",
                    chapter_num=chapter_num,
                    chapter_title=chapter_title
                ))
        
        return chunks
    
    def _extract_companies_act_structure(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract Companies Act structure - FIXED for actual format
        
        Format:
        CHAPTER I
        PRELIMINARY
        SECTIONS
        1. Short title...
        2. Definitions...
        """
        chunks = []
        
        # Pattern for CHAPTER markers
        chapter_pattern = r'CHAPTER\s+([IVX]+)\s*\n\s*([A-Z\s]+?)(?=\n|SECTIONS)'
        chapter_matches = list(re.finditer(chapter_pattern, text))
        
        print(f"   Found {len(chapter_matches)} chapters")
        
        if len(chapter_matches) == 0:
            return []
        
        for i, chapter_match in enumerate(chapter_matches):
            chapter_num = chapter_match.group(1).strip()
            chapter_title = chapter_match.group(2).strip()
            
            # Get chapter content
            start_pos = chapter_match.end()
            end_pos = chapter_matches[i + 1].start() if i + 1 < len(chapter_matches) else len(text)
            chapter_text = text[start_pos:end_pos]
            
            # Find sections: "1. Title", "2. Title", etc.
            section_pattern = r'\n\s*(\d+)\.\s+([^\n]{10,200})'
            section_matches = list(re.finditer(section_pattern, chapter_text))
            
            if len(section_matches) > 0:
                for j, section_match in enumerate(section_matches[:100]):
                    section_num = section_match.group(1)
                    section_title = section_match.group(2).strip()[:200]
                    
                    sec_start = section_match.start()
                    sec_end = section_matches[j + 1].start() if j + 1 < len(section_matches) else len(chapter_text)
                    sec_text = chapter_text[sec_start:sec_end].strip()[:5000]
                    
                    if len(sec_text) > 100:
                        chunks.append({
                            'type': 'section',
                            'chapter_number': chapter_num,
                            'chapter_title': chapter_title,
                            'section_number': section_num,
                            'section_title': section_title,
                            'text': sec_text,
                            'chunk_id': f"COMPANIES_ACT_CH{chapter_num}_SEC{section_num}"
                        })
            else:
                chunks.extend(self._chunk_large_text(
                    chapter_text,
                    prefix=f"COMPANIES_ACT_CH{chapter_num}",
                    chapter_num=chapter_num,
                    chapter_title=chapter_title
                ))
        
        return chunks
    
    def _fallback_chunking(self, text: str, doc_type: str) -> List[Dict[str, Any]]:
        """Simple chunking when structure detection fails"""
        print(f"   Using fallback chunking...")
        
        words = text.split()
        chunk_size = 500  # 500 words per chunk
        chunks = []
        
        for i in range(0, len(words), chunk_size):
            chunk_words = words[i:i + chunk_size]
            chunk_text = ' '.join(chunk_words)
            
            if len(chunk_text.strip()) > 100:
                chunk_num = (i // chunk_size) + 1
                
                chunks.append({
                    'type': 'text_chunk',
                    'chapter_number': f"PART{chunk_num // 20 + 1}",
                    'chapter_title': f"{doc_type} Content - Part {chunk_num // 20 + 1}",
                    'section_number': str(chunk_num),
                    'section_title': f"Section {chunk_num}",
                    'regulation_number': None,
                    'regulation_title': None,
                    'text': chunk_text[:5000],
                    'chunk_id': f"{doc_type}_CHUNK{chunk_num}"
                })
        
        return chunks
    
    def _chunk_large_text(self, text: str, prefix: str, chapter_num: str, chapter_title: str) -> List[Dict]:
        """Chunk large text that couldn't be structured"""
        chunks = []
        words = text.split()
        chunk_size = 500
        
        for i in range(0, len(words), chunk_size):
            chunk_words = words[i:i + chunk_size]
            chunk_text = ' '.join(chunk_words)
            
            if len(chunk_text.strip()) > 100:
                part_num = (i // chunk_size) + 1
                chunks.append({
                    'type': 'chapter_part',
                    'chapter_number': chapter_num,
                    'chapter_title': chapter_title,
                    'section_number': None,
                    'section_title': None,
                    'regulation_number': None,
                    'regulation_title': None,
                    'text': chunk_text[:5000],
                    'chunk_id': f"{prefix}_PART{part_num}"
                })
        
        return chunks
    
    def create_searchable_chunks(self, structured_chunks: List[Dict]) -> List[Dict[str, Any]]:
        """Create chunks optimized for semantic search"""
        print(f"\n📦 Creating searchable chunks...")
        
        searchable_chunks = []
        
        for chunk in structured_chunks:
            search_text = self._create_search_text(chunk)
            
            searchable_chunks.append({
                **chunk,
                'search_text': search_text,
                'chunk_length': len(search_text)
            })
        
        print(f"   ✅ Created {len(searchable_chunks)} searchable chunks")
        return searchable_chunks
    
    def _create_search_text(self, chunk: Dict) -> str:
        """Create search-optimized text"""
        parts = []
        
        if self.doc_type == "ICDR":
            if chunk.get('regulation_number'):
                parts.append(f"ICDR Regulation {chunk['regulation_number']}: {chunk.get('regulation_title', '')}")
            parts.append(f"Chapter {chunk['chapter_number']}: {chunk['chapter_title']}")
        else:
            if chunk.get('section_number'):
                parts.append(f"Section {chunk['section_number']}: {chunk.get('section_title', '')}")
            parts.append(f"Chapter {chunk['chapter_number']}: {chunk['chapter_title']}")
        
        parts.append(chunk['text'])
        
        return "\n".join(parts)


# ============================================================================
# NEO4J GRAPH STORAGE - FIXED WITH MERGE
# ============================================================================

class Neo4jLegalGraph:
    """Store legal documents in Neo4j with embeddings"""
    
    def __init__(self):
        self.driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
        print("✅ Neo4j connection established")
    
    def close(self):
        self.driver.close()
    
    def create_schema(self):
        """Create graph schema and indexes"""
        print("\n🏗️  Creating Neo4j schema...")
        
        with self.driver.session() as session:
            # Create indexes
            try:
                session.run("""
                    CREATE INDEX regulation_id IF NOT EXISTS
                    FOR (r:Regulation) ON (r.id)
                """)
            except:
                pass
            
            try:
                session.run("""
                    CREATE INDEX chapter_id IF NOT EXISTS
                    FOR (c:Chapter) ON (c.id)
                """)
            except:
                pass
            
            try:
                session.run("""
                    CREATE INDEX chunk_id IF NOT EXISTS
                    FOR (ch:LegalChunk) ON (ch.chunk_id)
                """)
            except:
                pass
            
            # Vector index
            try:
                session.run("""
                    CREATE VECTOR INDEX legal_chunk_embeddings IF NOT EXISTS
                    FOR (ch:LegalChunk) ON (ch.embedding)
                    OPTIONS {indexConfig: {
                        `vector.dimensions`: 768,
                        `vector.similarity_function`: 'cosine'
                    }}
                """)
                print("   ✅ Vector index created")
            except Exception as e:
                print(f"   ℹ️  Vector index: {str(e)[:100]}")
        
        print("   ✅ Schema created")
    
    def clear_all_data(self):
        """Clear ALL existing data"""
        print(f"\n🗑️  Clearing ALL existing data...")
        
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        
        print("   ✅ Database cleared")
    
    def ingest_document(self, doc_config: Dict, chunks: List[Dict], embeddings: List[List[float]]):
        """Ingest complete document with embeddings - USES MERGE"""
        print(f"\n💾 Ingesting {doc_config['short_name']} to Neo4j...")
        
        with self.driver.session() as session:
            # MERGE Regulation node (instead of CREATE)
            session.run("""
                MERGE (r:Regulation {id: $id})
                SET r.name = $name,
                    r.short_name = $short_name,
                    r.type = $type,
                    r.ingested_at = timestamp()
            """, {
                'id': doc_config['short_name'],
                'name': doc_config['regulation_name'],
                'short_name': doc_config['short_name'],
                'type': doc_config['type']
            })
            
            # Group chunks by chapter
            chapters = {}
            for chunk in chunks:
                ch_num = chunk['chapter_number']
                if ch_num not in chapters:
                    chapters[ch_num] = {
                        'title': chunk['chapter_title'],
                        'chunks': []
                    }
                chapters[ch_num]['chunks'].append(chunk)
            
            print(f"   Processing {len(chapters)} chapters...")
            
            # Ingest chapters and chunks
            total_chunks = 0
            for ch_num, ch_data in chapters.items():
                chapter_id = f"{doc_config['short_name']}_CH{ch_num}"
                
                # MERGE Chapter node
                session.run("""
                    MATCH (r:Regulation {id: $reg_id})
                    MERGE (c:Chapter {id: $chapter_id})
                    SET c.number = $number,
                        c.title = $title
                    MERGE (r)-[:HAS_CHAPTER]->(c)
                """, {
                    'reg_id': doc_config['short_name'],
                    'chapter_id': chapter_id,
                    'number': ch_num,
                    'title': ch_data['title']
                })
                
                # Ingest chunks
                for chunk in ch_data['chunks']:
                    chunk_embedding = embeddings[total_chunks]
                    
                    # MERGE LegalChunk node
                    session.run("""
                        MATCH (c:Chapter {id: $chapter_id})
                        MERGE (ch:LegalChunk {chunk_id: $chunk_id})
                        SET ch.type = $type,
                            ch.chapter_number = $chapter_number,
                            ch.chapter_title = $chapter_title,
                            ch.section_number = $section_number,
                            ch.section_title = $section_title,
                            ch.regulation_number = $regulation_number,
                            ch.regulation_title = $regulation_title,
                            ch.text = $text,
                            ch.search_text = $search_text,
                            ch.chunk_length = $chunk_length,
                            ch.embedding = $embedding
                        MERGE (c)-[:CONTAINS]->(ch)
                    """, {
                        'chapter_id': chapter_id,
                        'chunk_id': chunk['chunk_id'],
                        'type': chunk['type'],
                        'chapter_number': chunk['chapter_number'],
                        'chapter_title': chunk['chapter_title'],
                        'section_number': chunk.get('section_number'),
                        'section_title': chunk.get('section_title'),
                        'regulation_number': chunk.get('regulation_number'),
                        'regulation_title': chunk.get('regulation_title'),
                        'text': chunk['text'],
                        'search_text': chunk['search_text'],
                        'chunk_length': chunk['chunk_length'],
                        'embedding': chunk_embedding
                    })
                    
                    total_chunks += 1
                
                print(f"      ✅ Chapter {ch_num}: {len(ch_data['chunks'])} chunks")
            
            print(f"   ✅ Total chunks ingested: {total_chunks}")
    
    def get_statistics(self, regulation_type: str) -> Dict:
        """Get ingestion statistics"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (r:Regulation {type: $reg_type})
                OPTIONAL MATCH (r)-[:HAS_CHAPTER]->(c:Chapter)
                OPTIONAL MATCH (c)-[:CONTAINS]->(ch:LegalChunk)
                RETURN 
                    r.name as regulation_name,
                    count(DISTINCT c) as total_chapters,
                    count(ch) as total_chunks
            """, {'reg_type': regulation_type})
            
            record = result.single()
            if record:
                return {
                    'regulation_name': record['regulation_name'],
                    'total_chapters': record['total_chapters'],
                    'total_chunks': record['total_chunks']
                }
            return {}


# ============================================================================
# MAIN PIPELINE
# ============================================================================

def process_legal_document(doc_key: str):
    """Complete pipeline for one document"""
    doc_config = DOCUMENTS[doc_key]
    
    print("\n" + "=" * 80)
    print(f"📚 PROCESSING: {doc_config['regulation_name']}")
    print("=" * 80)
    
    # 1. Extract PDF
    extractor = LegalDocumentExtractor()
    gcs_uri = f"gs://{BUCKET_NAME}/{LEGAL_DOCS_FOLDER}/{doc_config['filename']}"
    
    pdf_data = extractor.extract_pdf_from_gcs(gcs_uri)
    
    # 2. Detect structure and create chunks
    chunker = LegalDocumentChunker(doc_type=doc_key)
    structured_chunks = chunker.detect_structure(pdf_data['full_text'])
    searchable_chunks = chunker.create_searchable_chunks(structured_chunks)
    
    # 3. Generate embeddings
    print("\n🧬 Generating embeddings...")
    embeddings_gen = EmbeddingsGenerator()
    
    search_texts = [chunk['search_text'] for chunk in searchable_chunks]
    embeddings = embeddings_gen.generate_embeddings(search_texts)
    
    print(f"   ✅ Generated {len(embeddings)} embeddings")
    
    # 4. Store in Neo4j
    neo4j = Neo4jLegalGraph()
    neo4j.ingest_document(doc_config, searchable_chunks, embeddings)
    
    # 5. Get statistics
    stats = neo4j.get_statistics(doc_config['type'])
    
    neo4j.close()
    
    return stats


def main():
    """Main execution"""
    print("\n" + "=" * 80)
    print("🚀 LEGAL DOCUMENT EMBEDDINGS PIPELINE")
    print("=" * 80)
    print(f"Project: {PROJECT_ID}")
    print(f"Bucket: {BUCKET_NAME}/{LEGAL_DOCS_FOLDER}")
    print("=" * 80)
    
    # Create Neo4j schema
    neo4j = Neo4jLegalGraph()
    
    # OPTIONAL: Clear all data first (uncomment if needed)
    # neo4j.clear_all_data()
    
    neo4j.create_schema()
    neo4j.close()
    
    # Process ICDR
    print("\n\n📘 PROCESSING ICDR REGULATIONS...")
    icdr_stats = process_legal_document("ICDR")
    
    time.sleep(2)
    
    # Process Companies Act
    print("\n\n📗 PROCESSING COMPANIES ACT 2013...")
    companies_stats = process_legal_document("COMPANIES_ACT")
    
    # Final summary
    print("\n" + "=" * 80)
    print("✅ PIPELINE COMPLETE")
    print("=" * 80)
    print("\nICDR Regulations:")
    print(f"  Chapters: {icdr_stats.get('total_chapters', 0)}")
    print(f"  Chunks: {icdr_stats.get('total_chunks', 0)}")
    
    print("\nCompanies Act, 2013:")
    print(f"  Chapters: {companies_stats.get('total_chapters', 0)}")
    print(f"  Chunks: {companies_stats.get('total_chunks', 0)}")
    
    total_chunks = icdr_stats.get('total_chunks', 0) + companies_stats.get('total_chunks', 0)
    print(f"\n📊 Total Legal Chunks with Embeddings: {total_chunks}")
    print("=" * 80)


if __name__ == "__main__":
    main()