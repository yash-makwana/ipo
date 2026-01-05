"""
Retrieval Agent - WITH FLEXIBLE PAGE FIELD SUPPORT
==================================================
Supports both 'page' and 'page_number' fields
"""

import time
from typing import Dict, Any, List
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state_models import ComplianceState, RetrievalOutput, update_agent_path
from embeddings_service import get_embeddings_service
from reranking_service import get_reranking_service
from semantic_legal_search import get_semantic_search
import numpy as np


class RetrievalAgent:
    """Retrieval Agent - Dual Source Retrieval"""
    
    def __init__(self, regulation_type: str = "ICDR"):
        """Initialize Retrieval Agent"""
        self.regulation_type = regulation_type
        self.embeddings = get_embeddings_service()
        self.reranker = get_reranking_service()
        
        try:
            self.semantic_search = get_semantic_search(regulation_type)
            print(f"✅ RetrievalAgent initialized with Neo4j search ({regulation_type})")
        except Exception as e:
            print(f"⚠️  Neo4j search not available: {e}")
            self.semantic_search = None
    
    def retrieve_from_user_drhp(
        self,
        requirement: str,
        document_chunks: List[Dict[str, Any]],
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant chunks from user's DRHP"""
        
        print(f"   🔍 Searching user DRHP for: {requirement[:60]}...")
        
        if not document_chunks:
            print(f"   ⚠️  No document chunks available")
            return []
        
        # ✅ DEBUG: Check what fields chunks have
        if document_chunks:
            sample_keys = list(document_chunks[0].keys())
            print(f"   📋 Chunk fields available: {sample_keys}")
        
        try:
            # Generate embedding for requirement
            query_embedding = self.embeddings.generate_single_embedding(requirement)
            
            # Generate embeddings for chunks
            chunk_texts = [c['text'] for c in document_chunks]
            chunk_embeddings = self.embeddings.generate_embeddings(chunk_texts)
            
            # Calculate similarities
            similarities = []
            for chunk_emb in chunk_embeddings:
                query_norm = np.linalg.norm(query_embedding)
                chunk_norm = np.linalg.norm(chunk_emb)
                
                if query_norm < 1e-10 or chunk_norm < 1e-10:
                    similarities.append(0.0)
                else:
                    sim = np.dot(query_embedding, chunk_emb) / (query_norm * chunk_norm)
                    similarities.append(float(sim))
            
            # Get top candidates
            top_indices = np.argsort(similarities)[-min(10, len(similarities)):][::-1]
            candidate_chunks = [document_chunks[i] for i in top_indices]
            candidate_scores = [similarities[i] for i in top_indices]
            
            print(f"   📊 Top scores: {[f'{s:.3f}' for s in candidate_scores[:3]]}")
            
            # Rerank for better accuracy
            if len(candidate_chunks) > 0:
                try:
                    reranked = self.reranker.rerank(
                        query=requirement,
                        documents=[c['text'] for c in candidate_chunks],
                        top_n=min(top_k, len(candidate_chunks))
                    )
                    
                    results = []
                    for result in reranked:
                        original_chunk = candidate_chunks[result['index']]
                        
                        # ✅ FLEXIBLE: Try multiple page field names
                        page = (original_chunk.get('page_number') or 
                               original_chunk.get('page') or 
                               original_chunk.get('pageNumber') or 0)
                        
                        results.append({
                            'text': original_chunk['text'],
                            'page_number': page,  # ✅ Always use page_number as standard
                            'page': page,  # ✅ Also set 'page' for compatibility
                            'relevance_score': result.get('relevance_score', result.get('score', 0.0)),
                            'source': 'USER_DRHP'
                        })
                    
                    print(f"   ✅ Found {len(results)} relevant chunks from user DRHP")
                    
                    # ✅ DEBUG: Show pages extracted
                    pages_found = [r['page_number'] for r in results if r['page_number'] != 0]
                    if pages_found:
                        print(f"   📄 Pages extracted: {pages_found}")
                    else:
                        print(f"   ⚠️  WARNING: No page numbers in extracted chunks!")
                    
                    return results
                    
                except Exception as e:
                    print(f"   ⚠️  Reranking failed: {e}, using embedding results")
                    results = []
                    for i in range(min(top_k, len(candidate_chunks))):
                        chunk = candidate_chunks[i]
                        page = (chunk.get('page_number') or 
                               chunk.get('page') or 
                               chunk.get('pageNumber') or 0)
                        
                        results.append({
                            'text': chunk['text'],
                            'page_number': page,
                            'page': page,
                            'relevance_score': candidate_scores[i],
                            'source': 'USER_DRHP'
                        })
                    return results
            
            return []
            
        except Exception as e:
            print(f"   ❌ Error retrieving from user DRHP: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def retrieve_from_neo4j(
        self,
        requirement: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant legal requirements from Neo4j"""
        
        print(f"   🔍 Searching Neo4j for legal requirements...")
        
        if not self.semantic_search:
            print(f"   ⚠️  Neo4j search not available")
            return []
        
        try:
            results = self.semantic_search.vector_search(
                query=requirement,
                top_k=top_k
            )
            
            if results:
                print(f"   ✅ Found {len(results)} legal requirements")
                for i, r in enumerate(results[:2], 1):
                    citation = r.get('citation', 'No citation')
                    score = r.get('similarity_score', 0)
                    print(f"      {i}. Score: {score:.3f} - {citation[:50]}...")
                
                # Format results
                formatted_results = []
                for r in results:
                    formatted_results.append({
                        'text': r.get('requirement_text', r.get('text', '')),
                        'similarity_score': r.get('similarity_score', 0.0),
                        'citation': r.get('citation', ''),
                        'chapter': r.get('chapter'),
                        'source': 'NEO4J_LEGAL_DB'
                    })
                
                return formatted_results
            else:
                print(f"   ℹ️  No legal requirements found in Neo4j")
                return []
                
        except Exception as e:
            print(f"   ❌ Error retrieving from Neo4j: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def execute(self, state: ComplianceState) -> ComplianceState:
        """Execute retrieval agent"""
        
        print(f"\n{'='*60}")
        print(f"🔍 RETRIEVAL AGENT")
        print(f"{'='*60}")
        print(f"Requirement: {state.requirement[:60]}...")
        
        start_time = time.time()
        
        # Update agent path
        state = update_agent_path(state, "RETRIEVAL")
        
        # Retrieve from user DRHP
        user_chunks = self.retrieve_from_user_drhp(
            requirement=state.requirement,
            document_chunks=state.user_document_chunks,
            top_k=3
        )
        
        # Retrieve from Neo4j legal database
        legal_reqs = self.retrieve_from_neo4j(
            requirement=state.requirement,
            top_k=3
        )
        
        # Update state
        state.user_relevant_chunks = user_chunks
        state.legal_requirements = legal_reqs
        
        # Store metadata
        elapsed_ms = (time.time() - start_time) * 1000
        
        # ✅ Extract pages for metadata
        user_pages = []
        if user_chunks:
            for chunk in user_chunks:
                page = chunk.get('page_number') or chunk.get('page', 0)
                if page and page != 0:
                    user_pages.append(page)
        user_pages = sorted(list(set(user_pages)))
        
        state.retrieval_metadata = {
            'user_chunks_count': len(user_chunks),
            'legal_requirements_count': len(legal_reqs),
            'retrieval_time_ms': elapsed_ms,
            'user_pages': user_pages,
            'legal_citations': [r.get('citation', '') for r in legal_reqs if r.get('citation')]
        }
        
        print(f"\n✅ Retrieval Complete:")
        print(f"   User DRHP chunks: {len(user_chunks)}")
        print(f"   Legal requirements: {len(legal_reqs)}")
        print(f"   Pages found: {user_pages}")
        print(f"   Time: {elapsed_ms:.0f}ms")
        
        return state