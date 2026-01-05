# reranking_service.py
# Advanced reranking for improved retrieval accuracy
# Uses multiple strategies to find the best evidence chunks

from typing import List, Dict, Any
import re
import math

class RerankingService:
    """
    Multi-strategy reranking service to improve retrieval accuracy

    Strategies:
    1. Semantic similarity (embeddings) - expects 'similarity' in matched_chunks entries
    2. Keyword matching (BM25-like lightweight)
    3. Contextual relevance (section-aware)
    4. Hybrid scoring (weighted combination)
    """

    def __init__(self):
        """Initialize reranking service"""
        print("✅ Reranking Service initialized")

        # Minimal compiled regex for tokenization
        self._token_re = re.compile(r"\w+")
        # Expand stop words a bit for better scoring
        self._stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'shall', 'will', 'must', 'may',
            'our', 'we', 'you', 'their', 'they', 'this', 'that', 'these', 'those'
        }

    def _tokenize(self, text: str) -> List[str]:
        """Simple word tokenizer returning lowercase tokens"""
        if not text:
            return []
        return [t.lower() for t in self._token_re.findall(text)]

    def calculate_keyword_score(self, requirement_text: str, chunk_text: str) -> float:
        """
        Calculate keyword overlap score (lightweight BM25-like approach)

        Args:
            requirement_text: Requirement text
            chunk_text: Document chunk text

        Returns:
            float: Keyword overlap score (0.0 to 1.0)
        """
        req_tokens = [t for t in self._tokenize(requirement_text) if t not in self._stop_words]
        if not req_tokens:
            return 0.0

        chunk_tokens = set(self._tokenize(chunk_text))
        matches = sum(1 for token in req_tokens if token in chunk_tokens)

        # Normalize by requirement length (with smoothing)
        return min(matches / max(len(req_tokens), 1), 1.0)

    def calculate_section_relevance(self, requirement: Dict[str, Any], chunk: Dict[str, Any]) -> float:
        """
        Calculate section-based relevance score. Boost if chunk contains
        keywords related to the requirement's reported section title.

        Args:
            requirement: Requirement dict with 'section_title' (optional)
            chunk: Chunk dict with 'text'

        Returns:
            float: Section relevance score (0.0 to 1.0)
        """
        section_keywords = {
            'capital structure': ['equity', 'shares', 'capital', 'issue', 'paidup'],
            'convertible debt': ['debenture', 'convertible', 'debt', 'bond'],
            'financial': ['revenue', 'profit', 'financial', 'statement', 'assets', 'liabilities'],
            'management': ['director', 'promoter', 'management', 'officer', 'ceo', 'cfo'],
            'risk': ['risk', 'uncertainty', 'threat'],
            'human resource': ['employee', 'attrition', 'training', 'manpower'],
            'manufacturing': ['plant', 'machinery', 'production', 'capacity']
        }

        req_title = (requirement.get('section_title') or "").lower()
        chunk_text = (chunk.get('text') or "").lower()

        # If requirement title contains known section name, check keywords
        best_score = 0.0
        for section_name, keywords in section_keywords.items():
            if section_name in req_title:
                keyword_count = sum(1 for kw in keywords if kw in chunk_text)
                best_score = keyword_count / max(len(keywords), 1)
                break

        return min(max(best_score, 0.0), 1.0)

    def calculate_position_score(self, chunk: Dict[str, Any], total_chunks: int) -> float:
        """
        Calculate position-based score (important info often appears early)

        Args:
            chunk: Chunk dict with 'chunk_id' (0-index)
            total_chunks: Total number of chunks

        Returns:
            float: Position score (0.0 to 1.0)
        """
        try:
            chunk_id = int(chunk.get('chunk_id', 0))
        except Exception:
            chunk_id = 0

        if total_chunks <= 0:
            return 0.0

        position_ratio = chunk_id / float(total_chunks)
        # Heuristic boosts
        if position_ratio < 0.10:
            return 0.30
        elif position_ratio < 0.30:
            return 0.15
        else:
            return 0.0

    def rerank_chunks(
        self,
        requirement: Dict[str, Any],
        matched_chunks: List[Dict[str, Any]],
        total_chunks: int,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Rerank matched chunks using hybrid scoring

        Args:
            requirement: Requirement dict
            matched_chunks: List of matched chunks with similarity scores (each item should have 'chunk' and 'similarity')
            total_chunks: Total number of chunks in document
            top_k: Number of top chunks to return

        Returns:
            List[Dict]: Reranked chunks (each has chunk, semantic_score, keyword_score, section_score, position_score, hybrid_score)
        """
        if not matched_chunks:
            return []

        reranked: List[Dict[str, Any]] = []

        for match in matched_chunks:
            chunk = match.get('chunk') or {}
            # semantic_score is expected to be between -1 and 1 or 0..1 depending on upstream; normalize to 0..1
            semantic_raw = match.get('similarity', 0.0)
            # handle possible negative cosine values by scaling
            semantic_score = float(semantic_raw)
            if semantic_score < -1.0:
                semantic_score = -1.0
            if semantic_score > 1.0:
                semantic_score = 1.0
            # normalize to 0..1
            semantic_score = (semantic_score + 1.0) / 2.0 if semantic_score < 0 else semantic_score

            keyword_score = self.calculate_keyword_score(requirement.get('requirement', ''), chunk.get('text', ''))
            section_score = self.calculate_section_relevance(requirement, chunk)
            position_score = self.calculate_position_score(chunk, total_chunks)

            # Weighted hybrid score (tunable)
            hybrid_score = (
                0.50 * semantic_score +
                0.30 * keyword_score +
                0.15 * section_score +
                0.05 * position_score
            )

            reranked.append({
                'chunk': chunk,
                'semantic_score': semantic_score,
                'keyword_score': keyword_score,
                'section_score': section_score,
                'position_score': position_score,
                'hybrid_score': hybrid_score,
                'original_rank': match.get('rank', 0)
            })

        # Sort by hybrid score (highest first) and return top_k
        reranked.sort(key=lambda x: x['hybrid_score'], reverse=True)
        return reranked[:max(1, top_k)]

    def rerank(self, query: str, documents: List[str], top_n: int = 3) -> List[Dict[str, Any]]:
        """
        Compatibility wrapper for ComplianceEngine:
        Accepts a raw query and a list of document texts and returns a list of dicts:
            [{ "index": int, "score": float, "text": str }, ...]

        This wrapper uses lightweight internal heuristics because no embeddings are available here.
        When used as part of a two-stage pipeline, the 'documents' will be a small set of candidate chunks
        (top-K by embeddings). This method therefore computes a combined score using lexical overlap and
        positional heuristics.

        Args:
            query: Requirement text to match
            documents: List of document chunk texts
            top_n: Number of top results to return

        Returns:
            List[Dict]: reranked results with index, score, text
        """
        if not documents:
            return []

        # Build matched_chunks with placeholder similarity (fallback lexical similarity)
        matched_chunks = []
        for i, doc in enumerate(documents):
            matched_chunks.append({
                'chunk': {
                    'chunk_id': i,
                    'text': doc,
                    'page_number': 1,
                    'metadata': {}
                },
                # Use simple lexical overlap as a proxy for semantic similarity when real similarity not provided
                'similarity': self._lexical_similarity(query, doc),
                'rank': i
            })

        requirement = {
            'requirement': query,
            'category': 'general',
            'section_title': ''
        }

        total_chunks = len(documents)
        reranked = self.rerank_chunks(requirement, matched_chunks, total_chunks, top_k=top_n)

        results: List[Dict[str, Any]] = []
        for item in reranked[:top_n]:
            c = item['chunk']
            results.append({
                'index': int(c.get('chunk_id', 0)),
                'score': float(item.get('hybrid_score', 0.0)),
                'text': c.get('text', '')
            })

        return results

    # --- Compatibility aliases for other callers ---
    def re_rank(self, query: str, documents: List[str], top_n: int = 3) -> List[Dict[str, Any]]:
        """Alias for rerank (alternate naming)"""
        return self.rerank(query, documents, top_n=top_n)

    def rank_documents(self, query: str, documents: List[str], top_k: int = 3) -> List[Dict[str, Any]]:
        """Another alias for rerank with top_k param name"""
        return self.rerank(query, documents, top_n=top_k)

    def rank(self, query: str, documents: List[str], top_k: int = 3) -> List[Dict[str, Any]]:
        """Simple alias - returns list of (index, score) tuples for backwards compatibility"""
        results = self.rerank(query, documents, top_n=top_k)
        return [(r['index'], r['score']) for r in results]

    def _lexical_similarity(self, query: str, doc: str) -> float:
        """
        Fallback lexical similarity: Jaccard-like overlap on tokens (0..1)
        Used only when embeddings/similarity are not provided upstream.
        """
        q_tokens = set(self._tokenize(query)) - self._stop_words
        d_tokens = set(self._tokenize(doc)) - self._stop_words
        if not q_tokens or not d_tokens:
            return 0.0
        inter = q_tokens.intersection(d_tokens)
        union = q_tokens.union(d_tokens)
        return float(len(inter)) / float(len(union))

    def explain_reranking(self, reranked_chunk: Dict[str, Any]) -> str:
        """
        Generate explanation for why a chunk was ranked highly

        Args:
            reranked_chunk: Reranked chunk with scores

        Returns:
            str: Human-readable explanation
        """
        scores = {
            'Semantic': reranked_chunk.get('semantic_score', 0.0),
            'Keyword': reranked_chunk.get('keyword_score', 0.0),
            'Section': reranked_chunk.get('section_score', 0.0),
            'Position': reranked_chunk.get('position_score', 0.0),
        }

        # Find dominant score type
        max_score_type = max(scores, key=scores.get)

        explanations = {
            'Semantic': 'High semantic similarity to requirement',
            'Keyword': 'Strong keyword match with requirement',
            'Section': 'Relevant to requirement section context',
            'Position': 'Located in document introduction'
        }

        return f"{explanations[max_score_type]} (hybrid score: {reranked_chunk.get('hybrid_score', 0.0):.3f})"


# Singleton
_reranking_service: RerankingService | None = None

def get_reranking_service() -> RerankingService:
    """Get or create reranking service singleton"""
    global _reranking_service
    if _reranking_service is None:
        _reranking_service = RerankingService()
    return _reranking_service


if __name__ == "__main__":
    """Test reranking service"""
    print("🧪 Testing Reranking Service...")

    service = get_reranking_service()

    # Test keyword scoring
    req_text = "The issuer must disclose equity share capital structure"
    chunk_text = "The equity share capital of the company consists of..."

    score = service.calculate_keyword_score(req_text, chunk_text)
    print(f"✅ Keyword score: {score:.3f}")

    # Test lexical similarity
    lex = service._lexical_similarity(req_text, chunk_text)
    print(f"✅ Lexical similarity: {lex:.3f}")

    # Test rerank wrapper
    docs = [
        "The equity share capital of the company consists of equity shares and preference shares.",
        "We have significant manufacturing capacity at our plant.",
        "The promoter holds 60% shareholding."
    ]
    res = service.rerank(req_text, docs, top_n=2)
    print("✅ Rerank results:", res)

    print("\n🎉 Reranking service test complete!")
