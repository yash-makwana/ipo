"""
Two-Phase Search Strategy
==========================
Combines fast semantic search with thorough exhaustive scan

PHASE 1: Quick Semantic Search (Fast)
- Uses embeddings for quick retrieval
- Good for catching obvious disclosures
- Returns in ~2-3 seconds

PHASE 2: Exhaustive Scan (Thorough)
- Triggered only when Phase 1 insufficient
- Scans ALL pages with keywords
- Returns in ~10-15 seconds

Result: Best of both worlds - speed + completeness

Author: IPO Compliance System
Date: January 2026
"""

from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import time


@dataclass
class TwoPhaseSearchResult:
    """Results from two-phase search"""
    phase_used: str  # 'semantic' or 'exhaustive' or 'hybrid'
    total_time_seconds: float
    evidence_found: bool
    evidence_pages: List[int]
    evidence_quality: str  # 'high', 'medium', 'low'
    semantic_results: List[Dict]  # From Phase 1
    exhaustive_results: Dict  # From Phase 2 (if triggered)
    recommendation: str  # 'PRESENT', 'INSUFFICIENT', 'MISSING', 'UNCLEAR'


class TwoPhaseSearchStrategy:
    """
    Implements intelligent two-phase search strategy
    
    Decision Logic:
    1. Try semantic search first (fast)
    2. If insufficient results → trigger exhaustive search
    3. Combine results intelligently
    """
    
    def __init__(
        self,
        semantic_search_fn,
        exhaustive_search_engine
    ):
        """
        Initialize two-phase strategy
        
        Args:
            semantic_search_fn: Function to call for semantic search
            exhaustive_search_engine: ExhaustiveSearchEngine instance
        """
        self.semantic_search = semantic_search_fn
        self.exhaustive_engine = exhaustive_search_engine
        
        # Thresholds for triggering exhaustive search
        self.min_semantic_chunks = 5  # Need at least 5 good chunks
        self.min_semantic_confidence = 0.6  # Or confidence > 0.6
        
        print("✅ Two-Phase Search Strategy initialized")
    
    # ========================================================================
    # MAIN SEARCH METHOD
    # ========================================================================
    
    def search(
        self,
        requirement: str,
        document_chunks: List[Dict],
        all_pages_dict: Dict[int, str],
        top_k: int = 20
    ) -> TwoPhaseSearchResult:
        """
        🎯 INTELLIGENT TWO-PHASE SEARCH
        
        Args:
            requirement: Legal obligation text
            document_chunks: Chunked document for semantic search
            all_pages_dict: Complete document for exhaustive search
            top_k: Top K chunks for semantic search
        
        Returns:
            TwoPhaseSearchResult with best evidence
        """
        
        start_time = time.time()
        
        print(f"\n   🔎 TWO-PHASE SEARCH STRATEGY")
        print(f"      Requirement: {requirement[:60]}...")
        
        # ====================================================================
        # PHASE 1: SEMANTIC SEARCH (Quick)
        # ====================================================================
        
        print(f"\n      📍 PHASE 1: Semantic Search (Quick)")
        phase1_start = time.time()
        
        semantic_results = self._run_semantic_search(
            requirement=requirement,
            document_chunks=document_chunks,
            top_k=top_k
        )
        
        phase1_time = time.time() - phase1_start
        print(f"         ✓ Found {len(semantic_results)} chunks in {phase1_time:.1f}s")
        
        # Evaluate semantic results quality
        semantic_quality = self._evaluate_semantic_quality(semantic_results)
        
        print(f"         ✓ Quality: {semantic_quality['quality']}")
        print(f"         ✓ Confidence: {semantic_quality['confidence']:.2f}")
        
        # ====================================================================
        # DECISION: Need Exhaustive Search?
        # ====================================================================
        
        needs_exhaustive = self._should_trigger_exhaustive(
            semantic_results=semantic_results,
            quality=semantic_quality
        )
        
        exhaustive_results = None
        phase_used = 'semantic'
        
        if needs_exhaustive:
            
            # ================================================================
            # PHASE 2: EXHAUSTIVE SCAN (Thorough)
            # ================================================================
            
            print(f"\n      🔬 PHASE 2: Exhaustive Scan (Triggered - Semantic insufficient)")
            phase2_start = time.time()
            
            exhaustive_results = self.exhaustive_engine.search_entire_document(
                pages_dict=all_pages_dict,
                requirement=requirement,
                min_relevance=0.2
            )
            
            phase2_time = time.time() - phase2_start
            print(f"         ✓ Scanned {exhaustive_results.total_pages_scanned} pages in {phase2_time:.1f}s")
            print(f"         ✓ Evidence on {exhaustive_results.pages_with_evidence} pages")
            
            phase_used = 'exhaustive'
        
        else:
            print(f"\n      ✓ PHASE 2: Skipped (Semantic results sufficient)")
        
        # ====================================================================
        # SYNTHESIZE RESULTS
        # ====================================================================
        
        final_result = self._synthesize_results(
            semantic_results=semantic_results,
            semantic_quality=semantic_quality,
            exhaustive_results=exhaustive_results,
            phase_used=phase_used
        )
        
        total_time = time.time() - start_time
        final_result.total_time_seconds = round(total_time, 2)
        
        print(f"\n      ✅ Search complete:")
        print(f"         Phase: {final_result.phase_used}")
        print(f"         Evidence: {final_result.evidence_found}")
        print(f"         Pages: {final_result.evidence_pages[:5]}")
        print(f"         Time: {total_time:.1f}s")
        
        return final_result
    
    # ========================================================================
    # PHASE 1: SEMANTIC SEARCH
    # ========================================================================
    
    def _run_semantic_search(
        self,
        requirement: str,
        document_chunks: List[Dict],
        top_k: int
    ) -> List[Dict]:
        """
        Run semantic search using existing infrastructure
        
        Args:
            requirement: Search query
            document_chunks: Document chunks
            top_k: Number of results
        
        Returns:
            List of relevant chunks
        """
        
        try:
            # Call the semantic search function provided
            results = self.semantic_search(
                query=requirement,
                top_k=top_k
            )
            
            return results if results else []
        
        except Exception as e:
            print(f"         ⚠️  Semantic search error: {e}")
            return []
    
    def _evaluate_semantic_quality(self, results: List[Dict]) -> Dict:
        """
        Evaluate quality of semantic search results
        
        Returns:
            {
                'quality': 'high'|'medium'|'low',
                'confidence': 0.0-1.0,
                'num_chunks': int,
                'unique_pages': int
            }
        """
        
        if not results:
            return {
                'quality': 'low',
                'confidence': 0.0,
                'num_chunks': 0,
                'unique_pages': 0
            }
        
        num_chunks = len(results)
        
        # Extract unique pages
        unique_pages = set()
        for chunk in results:
            page = chunk.get('page_number', chunk.get('page'))
            if page:
                unique_pages.add(page)
        
        num_unique_pages = len(unique_pages)
        
        # Calculate confidence based on:
        # 1. Number of chunks
        # 2. Page diversity
        # 3. Relevance scores (if available)
        
        confidence = 0.0
        
        # Factor 1: Chunk count (max 0.4)
        confidence += min(num_chunks / 10, 0.4)
        
        # Factor 2: Page diversity (max 0.3)
        confidence += min(num_unique_pages / 5, 0.3)
        
        # Factor 3: Average relevance score (max 0.3)
        if results and 'score' in results[0]:
            avg_score = sum(r.get('score', 0) for r in results) / len(results)
            confidence += avg_score * 0.3
        else:
            confidence += 0.2  # Default bonus if no scores
        
        # Determine quality category
        if confidence >= 0.7 and num_chunks >= 5:
            quality = 'high'
        elif confidence >= 0.4 and num_chunks >= 3:
            quality = 'medium'
        else:
            quality = 'low'
        
        return {
            'quality': quality,
            'confidence': min(confidence, 1.0),
            'num_chunks': num_chunks,
            'unique_pages': num_unique_pages
        }
    
    # ========================================================================
    # DECISION LOGIC
    # ========================================================================
    
    def _should_trigger_exhaustive(
        self,
        semantic_results: List[Dict],
        quality: Dict
    ) -> bool:
        """
        Decide whether to trigger exhaustive search
        
        Triggers if:
        - < 5 semantic chunks found
        - OR confidence < 0.6
        - OR quality is 'low'
        
        Args:
            semantic_results: Results from Phase 1
            quality: Quality evaluation
        
        Returns:
            True if exhaustive search needed
        """
        
        # Check chunk count
        if len(semantic_results) < self.min_semantic_chunks:
            return True
        
        # Check confidence
        if quality['confidence'] < self.min_semantic_confidence:
            return True
        
        # Check quality category
        if quality['quality'] == 'low':
            return True
        
        return False
    
    # ========================================================================
    # RESULT SYNTHESIS
    # ========================================================================
    
    def _synthesize_results(
        self,
        semantic_results: List[Dict],
        semantic_quality: Dict,
        exhaustive_results,
        phase_used: str
    ) -> TwoPhaseSearchResult:
        """
        Synthesize results from both phases
        
        Combines semantic and exhaustive results intelligently
        """
        
        # Determine evidence status
        if phase_used == 'exhaustive':
            # Use exhaustive results
            evidence_found = exhaustive_results.pages_with_evidence > 0
            evidence_pages = exhaustive_results.evidence_pages
            evidence_quality = exhaustive_results.confidence
            
            # Recommendation based on exhaustive search
            if not evidence_found:
                recommendation = 'MISSING'  # High confidence MISSING
            elif evidence_quality == 'high':
                recommendation = 'PRESENT'  # Likely complete
            else:
                recommendation = 'INSUFFICIENT'  # Found but may be incomplete
        
        else:
            # Use semantic results
            evidence_found = len(semantic_results) > 0
            
            # Extract pages from semantic results
            evidence_pages = []
            for chunk in semantic_results:
                page = chunk.get('page_number', chunk.get('page'))
                if page and page not in evidence_pages:
                    evidence_pages.append(page)
            
            evidence_quality = semantic_quality['quality']
            
            # Recommendation based on semantic search
            if not evidence_found:
                recommendation = 'UNCLEAR'  # Not confident without exhaustive
            elif semantic_quality['quality'] == 'high':
                recommendation = 'PRESENT'
            else:
                recommendation = 'INSUFFICIENT'
        
        return TwoPhaseSearchResult(
            phase_used=phase_used,
            total_time_seconds=0.0,  # Will be set by caller
            evidence_found=evidence_found,
            evidence_pages=sorted(evidence_pages),
            evidence_quality=evidence_quality,
            semantic_results=semantic_results,
            exhaustive_results=exhaustive_results,
            recommendation=recommendation
        )
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def get_best_evidence(self, result: TwoPhaseSearchResult, max_items: int = 10) -> List[Dict]:
        """
        Get best evidence from search results
        
        Prioritizes exhaustive results if available, else uses semantic
        
        Returns:
            List of evidence items with page numbers
        """
        
        if result.phase_used == 'exhaustive' and result.exhaustive_results:
            # Convert exhaustive matches to standard format
            evidence = []
            for match in result.exhaustive_results.evidence_matches[:max_items]:
                evidence.append({
                    'page_number': match.page_number,
                    'text': match.text_snippet,
                    'relevance': match.relevance_score,
                    'source': 'exhaustive'
                })
            return evidence
        
        else:
            # Use semantic results
            return result.semantic_results[:max_items]
    
    def format_summary(self, result: TwoPhaseSearchResult) -> str:
        """Format search summary for logging"""
        
        lines = [
            f"TWO-PHASE SEARCH SUMMARY:",
            f"- Phase used: {result.phase_used.upper()}",
            f"- Evidence found: {result.evidence_found}",
            f"- Evidence pages: {result.evidence_pages[:10]}",
            f"- Evidence quality: {result.evidence_quality}",
            f"- Recommendation: {result.recommendation}",
            f"- Total time: {result.total_time_seconds}s"
        ]
        
        if result.phase_used == 'semantic':
            lines.append(f"- Semantic chunks: {len(result.semantic_results)}")
        
        if result.phase_used == 'exhaustive':
            ex = result.exhaustive_results
            lines.append(f"- Pages scanned: {ex.total_pages_scanned}")
            lines.append(f"- Pages with evidence: {ex.pages_with_evidence}")
        
        return '\n'.join(lines)


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def get_two_phase_strategy(semantic_search_fn, exhaustive_search_engine):
    """
    Create two-phase search strategy
    
    Args:
        semantic_search_fn: Function for semantic search
        exhaustive_search_engine: ExhaustiveSearchEngine instance
    
    Returns:
        TwoPhaseSearchStrategy instance
    """
    return TwoPhaseSearchStrategy(semantic_search_fn, exhaustive_search_engine)


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """Test two-phase strategy"""
    
    print("="*80)
    print("🧪 TESTING TWO-PHASE SEARCH STRATEGY")
    print("="*80)
    
    # Mock semantic search function
    def mock_semantic_search(query, top_k=20):
        # Return few results to trigger exhaustive
        return [
            {'page_number': 1, 'text': 'Generic intro...', 'score': 0.3},
            {'page_number': 2, 'text': 'Table of contents...', 'score': 0.2}
        ]
    
    # Mock exhaustive engine
    from exhaustive_search_engine import get_exhaustive_search_engine
    exhaustive_engine = get_exhaustive_search_engine()
    
    # Create strategy
    strategy = get_two_phase_strategy(mock_semantic_search, exhaustive_engine)
    
    # Mock pages
    mock_pages = {
        1: "Draft Red Herring Prospectus. Company XYZ.",
        47: "R&D facilities in Bangalore. R&D expenditure ₹5.2 crore."
    }
    
    # Test search
    result = strategy.search(
        requirement="Disclose R&D facilities",
        document_chunks=[],
        all_pages_dict=mock_pages,
        top_k=20
    )
    
    print("\n" + strategy.format_summary(result))
    
    print("\n" + "="*80)
    print("✅ TEST COMPLETE")
    print("="*80)