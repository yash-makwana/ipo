"""
Semantic Legal Search Service - WITH SMART RETRIEVAL
===================================================
"""
from sentence_transformers import SentenceTransformer
from neo4j import GraphDatabase
import os
import re
import numpy as np
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv('.env-local')

NEO4J_URI = os.environ.get('NEO4J_URI')
NEO4J_USER = os.environ.get('NEO4J_USER')
NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD')


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity"""
    try:
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    except Exception as e:
        print(f"⚠️  Cosine similarity error: {e}")
        return 0.0


def extract_chapter_from_source(source_clause: str) -> Optional[str]:
    """Extract chapter from source_clause"""
    if not source_clause:
        return None
    
    match = re.search(r'(Chapter [IVXLCDM]+|Schedule [IVXLCDM]+)', source_clause, re.IGNORECASE)
    if match:
        return match.group(1)
    return None


class SemanticLegalSearch:
    """Semantic search with SMART RETRIEVAL"""
    
    def __init__(self, regulation_type='ICDR'):
        """Initialize"""
        self.regulation_type = regulation_type
        
        self.regulation_mapping = {
            'ICDR': 'ICDR_2018',
            'Companies Act': 'COMPANIES_ACT_2013'
        }
        
        print(f"🔄 Loading local embedding model for semantic search...")
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        
        self.driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
        
        print(f"✅ Semantic Legal Search initialized for {regulation_type}")
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding"""
        try:
            embedding = self.embedding_model.encode(
                text,
                show_progress_bar=False,
                convert_to_numpy=True
            )
            return embedding
        except Exception as e:
            print(f"❌ Embedding error: {e}")
            return np.zeros(384)
    
    def vector_search(
        self, 
        query: str, 
        top_k: int = 20,  # 🔴 FIXED: Increased from 5 to 20
        chapter_filter: Optional[List[str]] = None,
        section_filter: Optional[List[str]] = None,
        mandatory_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Vector search for obligations - FIXED to return more results"""
        
        try:
            query_embedding = self.generate_embedding(query)
            query_embedding_list = query_embedding.tolist()
            
            db_regulation = self.regulation_mapping.get(self.regulation_type, self.regulation_type)
            
            cypher_query = """
            MATCH (o:Obligation)
            WHERE o.regulation = $regulation_type
            AND o.embedding IS NOT NULL
            """
            
            if mandatory_only:
                cypher_query += " AND o.mandatory = true"
            
            cypher_query += """
            RETURN 
                o.requirement_text AS requirement_text,
                o.source_clause AS source_clause,
                o.mandatory AS mandatory,
                o.obligation_type AS obligation_type,
                o.subject AS subject,
                o.action AS action,
                o.object AS object,
                o.confidence AS confidence,
                o.embedding AS embedding
            LIMIT 200
            """
            
            params = {'regulation_type': db_regulation}
            
            with self.driver.session() as session:
                result = session.run(cypher_query, **params)
                
                candidates = []
                for record in result:
                    embedding = record.get('embedding')
                    if not embedding:
                        continue
                    
                    similarity = cosine_similarity(query_embedding_list, embedding)
                    
                    if similarity < 0.15:
                        continue
                    
                    source_clause = record.get('source_clause', 'No citation')
                    chapter = extract_chapter_from_source(source_clause)
                    
                    if chapter_filter:
                        if not chapter or chapter not in chapter_filter:
                            continue
                    
                    candidates.append({
                        'requirement_text': record['requirement_text'],
                        'citation': source_clause,
                        'source_clause': source_clause,
                        'chapter': chapter,
                        'regulation': db_regulation,
                        'mandatory': record.get('mandatory', False),
                        'obligation_type': record.get('obligation_type'),
                        'subject': record.get('subject'),
                        'action': record.get('action'),
                        'object': record.get('object'),
                        'confidence': record.get('confidence'),
                        'similarity_score': similarity
                    })
                
                candidates.sort(key=lambda x: x['similarity_score'], reverse=True)
                return candidates[:top_k]
                
        except Exception as e:
            print(f"❌ Vector search error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_obligations_by_chapter(
        self,
        chapter: str,
        section: Optional[str] = None,
        mandatory_only: bool = False,
        limit: int = 30,
        relevance_query: Optional[str] = None  # ✅ NEW PARAMETER
    ) -> List[Dict[str, Any]]:
        """
        Get obligations with SMART RETRIEVAL
        
        Args:
            chapter: Chapter name
            section: Not used
            mandatory_only: Only mandatory
            limit: Max results
            relevance_query: Query for smart filtering
        """
        try:
            db_regulation = self.regulation_mapping.get(self.regulation_type, self.regulation_type)
            
            cypher_query = """
            MATCH (o:Obligation)
            WHERE o.regulation = $regulation_type
            AND o.source_clause =~ $chapter_pattern
            """
            
            if mandatory_only:
                cypher_query += " AND o.mandatory = true"
            
            cypher_query += """
            RETURN 
                o.requirement_text AS requirement_text,
                o.source_clause AS source_clause,
                o.mandatory AS mandatory,
                o.obligation_type AS obligation_type,
                o.subject AS subject,
                o.embedding AS embedding
            ORDER BY o.source_clause
            """
            
            chapter_pattern = f".*{re.escape(chapter)}.*"
            
            params = {
                'regulation_type': db_regulation,
                'chapter_pattern': chapter_pattern
            }
            
            with self.driver.session() as session:
                result = session.run(cypher_query, **params)
                
                obligations = []
                for record in result:
                    source_clause = record.get('source_clause', 'No citation')
                    chapter_extracted = extract_chapter_from_source(source_clause)
                    
                    obligations.append({
                        'requirement_text': record['requirement_text'],
                        'citation': source_clause,
                        'source_clause': source_clause,
                        'chapter': chapter_extracted,
                        'regulation': db_regulation,
                        'mandatory': record.get('mandatory', False),
                        'obligation_type': record.get('obligation_type'),
                        'subject': record.get('subject'),
                        'embedding': record.get('embedding')
                    })
                
                # ✅ SMART FILTERING with relevance query
                if relevance_query and obligations:
                    print(f"   🎯 Smart filtering: {len(obligations)} obligations → top {limit} relevant")
                    query_embedding = self.generate_embedding(relevance_query)
                    
                    # Calculate relevance scores
                    for obl in obligations:
                        if obl.get('embedding'):
                            similarity = cosine_similarity(query_embedding.tolist(), obl['embedding'])
                            obl['relevance_score'] = similarity
                        else:
                            obl['relevance_score'] = 0.0
                    
                    # Sort by relevance
                    obligations.sort(key=lambda x: x['relevance_score'], reverse=True)
                    obligations = obligations[:limit]
                    
                    # Clean up embeddings
                    for obl in obligations:
                        obl.pop('embedding', None)
                else:
                    # No smart filtering, just take first N
                    obligations = obligations[:limit]
                    for obl in obligations:
                        obl.pop('embedding', None)
                
                return obligations
                
        except Exception as e:
            print(f"❌ Chapter query error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_available_chapters(self) -> List[str]:
        """Get available chapters"""
        try:
            db_regulation = self.regulation_mapping.get(self.regulation_type, self.regulation_type)
            
            cypher_query = """
            MATCH (o:Obligation)
            WHERE o.regulation = $regulation_type
            AND o.source_clause IS NOT NULL
            RETURN DISTINCT o.source_clause AS source_clause
            """
            
            with self.driver.session() as session:
                result = session.run(cypher_query, regulation_type=db_regulation)
                
                chapters = set()
                for record in result:
                    chapter = extract_chapter_from_source(record['source_clause'])
                    if chapter:
                        chapters.add(chapter)
                
                return sorted(list(chapters))
                
        except Exception as e:
            print(f"❌ Error fetching chapters: {e}")
            return []
    
    def close(self):
        """Close connection"""
        if self.driver:
            self.driver.close()


# Singleton
_semantic_search_instances = {}

def get_semantic_search(regulation_type='ICDR'):
    """Get or create instance"""
    global _semantic_search_instances
    
    if regulation_type not in _semantic_search_instances:
        _semantic_search_instances[regulation_type] = SemanticLegalSearch(regulation_type)
    
    return _semantic_search_instances[regulation_type]