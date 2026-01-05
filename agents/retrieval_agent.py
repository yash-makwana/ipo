"""
Retrieval Agent - SIMPLIFIED (No Page Extraction)
==================================================
Retrieves relevant chunks from DRHP for compliance checking.

SIMPLIFIED: Removed page number extraction since:
- System B (Engine 3) already extracts page numbers correctly from PDF footers
- No need to duplicate page extraction logic
- Cleaner, faster code

Author: IPO Compliance System
Date: January 2026
"""

import time
from typing import Dict, List
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state_models import ComplianceState, update_agent_path


class RetrievalAgent:
    """
    Retrieval Agent - Fetches relevant DRHP content
    
    Simplified version without page number extraction
    (Engine 3 handles page numbers for System B)
    """
    
    def __init__(self, regulation_type: str = "ICDR"):
        """Initialize Retrieval Agent"""
        self.regulation_type = regulation_type
        print(f"✅ RetrievalAgent initialized (simplified - no page extraction)")
    
    def execute(self, state: ComplianceState) -> ComplianceState:
        """
        Execute retrieval step
        
        Retrieves relevant DRHP chunks for the obligation
        
        Args:
            state: Current compliance state
        
        Returns:
            Updated state with retrieved chunks
        """
        
        # Update agent path
        state = update_agent_path(state, "RetrievalAgent")
        
        # Check if we have semantic search available
        if not hasattr(self, 'semantic_search') or not self.semantic_search:
            # Use basic keyword matching as fallback
            state.user_relevant_chunks = self._keyword_retrieval(
                requirement=state.requirement,
                document_chunks=state.user_document_chunks
            )
        else:
            # Use semantic search
            state.user_relevant_chunks = self._semantic_retrieval(
                requirement=state.requirement,
                document_chunks=state.user_document_chunks
            )
        
        # 🔴 CRITICAL: Ensure all_pages_dict is populated
        # This is needed for exhaustive search in analysis agent
        if not hasattr(state, 'all_pages_dict') or not state.all_pages_dict:
            state.all_pages_dict = self._build_pages_dict(state.user_document_chunks)
        
        return state
    
    def _semantic_retrieval(
        self,
        requirement: str,
        document_chunks: List[Dict]
    ) -> List[Dict]:
        """
        Semantic retrieval using embeddings
        
        Args:
            requirement: Legal obligation text
            document_chunks: DRHP chunks
        
        Returns:
            List of relevant chunks (top 20 for better coverage)
        """
        
        try:
            # Use semantic search if available
            results = self.semantic_search.search(
                query=requirement,
                top_k=20  # 🔴 FIX: Was 5, now 20 for better coverage
            )
            
            return results if results else []
        
        except Exception as e:
            print(f"      ⚠️  Semantic retrieval error: {e}")
            # Fallback to keyword matching
            return self._keyword_retrieval(requirement, document_chunks)
    
    def _keyword_retrieval(
        self,
        requirement: str,
        document_chunks: List[Dict]
    ) -> List[Dict]:
        """
        Simple keyword-based retrieval (fallback)
        
        Args:
            requirement: Legal obligation text
            document_chunks: DRHP chunks
        
        Returns:
            List of relevant chunks
        """
        
        import re
        
        # Extract keywords
        keywords = self._extract_keywords(requirement)
        
        # Score chunks
        scored_chunks = []
        for chunk in document_chunks:
            text = chunk.get('text', '').lower()
            
            # Count keyword matches
            matches = sum(1 for kw in keywords if kw.lower() in text)
            
            if matches > 0:
                scored_chunks.append({
                    'chunk': chunk,
                    'score': matches / len(keywords)
                })
        
        # Sort by score
        scored_chunks.sort(key=lambda x: x['score'], reverse=True)
        
        # Return top 20
        return [sc['chunk'] for sc in scored_chunks[:20]]
    
    def _extract_keywords(self, requirement: str) -> List[str]:
        """Extract keywords from requirement"""
        
        import re
        
        # Remove common stop words
        stop_words = {
            'the', 'and', 'for', 'with', 'this', 'that', 'from',
            'shall', 'should', 'must', 'may', 'can', 'disclose'
        }
        
        # Extract words
        words = re.findall(r'\b[a-zA-Z]{4,}\b', requirement.lower())
        
        # Filter
        keywords = [w for w in words if w not in stop_words]
        
        return keywords[:10]  # Top 10 keywords
    
    def _build_pages_dict(self, chunks: List[Dict]) -> Dict[int, str]:
        """
        Build complete pages dictionary from chunks
        
        🔴 CRITICAL: This is needed for exhaustive search
        
        Args:
            chunks: Document chunks
        
        Returns:
            {page_num: page_text} dictionary
        """
        
        pages_dict = {}
        
        for chunk in chunks:
            page_num = chunk.get('page_number', chunk.get('page', 0))
            text = chunk.get('text', '')
            
            if page_num > 0:
                if page_num in pages_dict:
                    pages_dict[page_num] += "\n" + text
                else:
                    pages_dict[page_num] = text
        
        return pages_dict


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def get_retrieval_agent(regulation_type: str = "ICDR"):
    """Factory function to create retrieval agent"""
    return RetrievalAgent(regulation_type)


# ============================================================================
# BACKWARD COMPATIBILITY
# ============================================================================

# This matches the interface your code expects
# Can be imported as: from agents.retrieval_agent import RetrievalAgent