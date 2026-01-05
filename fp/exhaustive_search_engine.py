"""
Exhaustive Document Search Engine
==================================
Searches EVERY page of DRHP for evidence before allowing any "MISSING" conclusion.

This is the core fix that prevents page-1 bias and false negatives.

Usage:
    engine = ExhaustiveSearchEngine()
    results = engine.search_entire_document(
        pages_dict=pages_dict,
        requirement="Disclose R&D facilities and expenditure"
    )

Author: IPO Compliance System - Fixed Version
Date: January 2026
"""

import re
from typing import Dict, List, Tuple, Set, Any
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class EvidenceMatch:
    """Single evidence match from document"""
    page_number: int
    text_snippet: str
    keyword_matches: List[str]
    relevance_score: float
    context_sentences: List[str]


@dataclass
class SearchResult:
    """Complete search results from exhaustive scan"""
    total_pages_scanned: int
    pages_with_evidence: int
    evidence_pages: List[int]
    evidence_matches: List[EvidenceMatch]
    keywords_used: List[str]
    search_time_seconds: float
    confidence: str  # 'high', 'medium', 'low'


class ExhaustiveSearchEngine:
    """
    Searches ENTIRE DRHP document for evidence
    
    Key Features:
    - Scans ALL pages, not just top semantic results
    - Keyword-based + semantic understanding
    - Returns page-level evidence with citations
    - Prevents premature "MISSING" conclusions
    """
    
    def __init__(self):
        """Initialize search engine"""
        
        # Domain-specific keyword patterns for IPO compliance
        # Enhanced with comprehensive ICDR/Companies Act terminology
        self.domain_patterns = {
            'r&d': [
                'research', 'development', 'r&d', 'r & d', 'r and d', 'innovation',
                'technical center', 'research center', 'development facility',
                'r\u0026d expenditure', 'r\u0026d spend', 'r\u0026d investment'
            ],
            'revenue': [
                'revenue', 'sales', 'turnover', 'income', 'topline', 'top line',
                'gross income', 'operating revenue', 'net sales', 'total revenue',
                'revenue from operations', 'sale of goods', 'sale of services'
            ],
            'facilities': [
                'facility', 'facilities', 'plant', 'manufacturing unit', 'factory',
                'location', 'premises', 'establishment', 'site', 'registered office',
                'corporate office', 'branch office', 'production facility'
            ],
            'subsidiaries': [
                'subsidiary', 'subsidiaries', 'group company', 'associate',
                'joint venture', 'jv', 'wholly owned', 'step down subsidiary',
                'material subsidiary', 'foreign subsidiary', 'unlisted subsidiary'
            ],
            'directors': [
                'director', 'board', 'board of directors', 'management',
                'key managerial', 'kmp', 'key managerial personnel',
                'board member', 'independent director', 'executive director',
                'non-executive director', 'woman director', 'nominee director'
            ],
            'employees': [
                'employee', 'workforce', 'personnel', 'headcount', 'staff',
                'manpower', 'human resources', 'team size', 'attrition',
                'employee strength', 'permanent employee', 'contract employee'
            ],
            'customers': [
                'customer', 'client', 'buyer', 'purchaser', 'end user',
                'consumer', 'clientele', 'customer concentration',
                'top customer', 'single customer', 'customer base'
            ],
            'suppliers': [
                'supplier', 'vendor', 'procure', 'procurement', 'purchase',
                'raw material', 'sourcing', 'supplier concentration',
                'single supplier', 'vendor base', 'material supplier'
            ],
            'export': [
                'export', 'overseas', 'foreign', 'international', 'abroad',
                'cross border', 'global', 'export revenue', 'export sales',
                'overseas market', 'international market'
            ],
            'product': [
                'product', 'sku', 'offering', 'portfolio', 'product line',
                'product range', 'product mix', 'product category',
                'product segment', 'goods', 'merchandise'
            ],
            'risk': [
                'risk', 'risk factor', 'threat', 'concern', 'challenge',
                'uncertainty', 'exposure', 'vulnerability', 'contingent liability',
                'material risk', 'business risk', 'operational risk'
            ],
            'financial_metrics': [
                'ebitda', 'ebit', 'profit', 'pat', 'pbt', 'margin',
                'gross margin', 'net margin', 'operating margin',
                'debt', 'equity', 'roce', 'roe', 'roa', 'roic',
                'net worth', 'assets', 'liabilities', 'working capital',
                'current ratio', 'debt equity ratio', 'eps', 'nav'
            ],
            'related_party': [
                'related party', 'rpt', 'related party transaction',
                'arm\'s length', 'promoter group', 'promoter',
                'related party disclosure', 'material rpt'
            ],
            'intellectual_property': [
                'trademark', 'patent', 'copyright', 'ip', 'intellectual property',
                'brand', 'proprietary', 'trade secret', 'design registration',
                'patent application', 'trademark registration'
            ],
            'compliance_legal': [
                'compliance', 'regulation', 'sebi', 'icdr', 'companies act',
                'statutory', 'regulatory', 'filing', 'disclosure',
                'prospectus', 'drhp', 'roc', 'registrar of companies'
            ],
            'litigation': [
                'litigation', 'lawsuit', 'legal proceeding', 'dispute',
                'arbitration', 'tribunal', 'court case', 'legal notice',
                'material litigation', 'pending litigation', 'threatened litigation'
            ],
            'promoters': [
                'promoter', 'promoter group', 'promoter holding',
                'promoter contribution', 'promoter shareholding',
                'key promoter', 'individual promoter', 'corporate promoter'
            ],
            'objects_of_issue': [
                'object of issue', 'use of proceeds', 'fund utilization',
                'capital expenditure', 'capex', 'debt repayment',
                'working capital', 'general corporate purpose',
                'issue proceeds', 'net proceeds'
            ],
            'share_capital': [
                'share capital', 'equity share', 'authorized capital',
                'issued capital', 'subscribed capital', 'paid up capital',
                'face value', 'par value', 'share premium',
                'preference share', 'equity dilution'
            ],
            'dividends': [
                'dividend', 'dividend policy', 'dividend payout',
                'dividend distribution', 'interim dividend', 'final dividend',
                'dividend per share', 'payout ratio'
            ],
            'corporate_governance': [
                'corporate governance', 'audit committee', 'nomination committee',
                'remuneration committee', 'stakeholder committee',
                'code of conduct', 'vigil mechanism', 'whistle blower'
            ],
            'material_contracts': [
                'material contract', 'agreement', 'mou', 'memorandum',
                'collaboration agreement', 'licensing agreement',
                'supply agreement', 'customer agreement'
            ],
            'insurance': [
                'insurance', 'insurance policy', 'insurance coverage',
                'insured', 'insurable interest', 'key man insurance',
                'property insurance', 'marine insurance'
            ],
            'quality_certifications': [
                'iso', 'certificate', 'certification', 'accreditation',
                'quality standard', 'iso certified', 'quality control',
                'quality assurance', 'qa', 'qc'
            ],
            'expansion_plans': [
                'expansion', 'expansion plan', 'growth plan', 'capex plan',
                'new facility', 'capacity expansion', 'geographical expansion',
                'new market', 'diversification'
            ],
            'competition': [
                'competitor', 'competition', 'competitive landscape',
                'market share', 'competitive advantage', 'peer',
                'industry player', 'market position'
            ],
            'regulatory_approvals': [
                'approval', 'license', 'permit', 'registration',
                'regulatory approval', 'statutory approval',
                'government approval', 'clearance', 'consent'
            ],
            'taxation': [
                'tax', 'income tax', 'gst', 'indirect tax', 'direct tax',
                'tax assessment', 'tax dispute', 'tax benefit',
                'tax holiday', 'withholding tax', 'advance tax'
            ]
        }
        
        print("✅ ExhaustiveSearchEngine initialized")
    
    # ========================================================================
    # MAIN SEARCH METHOD
    # ========================================================================
    
    def search_entire_document(
        self,
        pages_dict: Dict[int, str],
        requirement: str,
        min_relevance: float = 0.2
    ) -> SearchResult:
        """
        🔍 SEARCH EVERY PAGE OF DOCUMENT
        
        This is the core method that prevents false negatives.
        
        Args:
            pages_dict: {page_num: page_text} for entire document
            requirement: Legal obligation text to search for
            min_relevance: Minimum relevance score (0.0-1.0)
        
        Returns:
            SearchResult with all matching pages and evidence
        """
        
        import time
        start_time = time.time()
        
        print(f"\n   🔍 EXHAUSTIVE SEARCH INITIATED")
        print(f"      Requirement: {requirement[:80]}...")
        
        # Extract search keywords from obligation
        keywords = self._extract_keywords(requirement)
        print(f"      Keywords: {', '.join(keywords[:8])}")
        
        # Initialize results
        evidence_matches = []
        pages_with_evidence = set()
        
        # SCAN EVERY SINGLE PAGE
        total_pages = len(pages_dict)
        print(f"      Scanning {total_pages} pages...")
        
        for page_num, page_text in sorted(pages_dict.items()):
            
            # Find matches on this page
            matches = self._find_matches_on_page(
                page_num=page_num,
                page_text=page_text,
                keywords=keywords,
                requirement=requirement
            )
            
            if matches and matches.relevance_score >= min_relevance:
                evidence_matches.append(matches)
                pages_with_evidence.add(page_num)
        
        # Sort by relevance
        evidence_matches.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            pages_with_evidence=len(pages_with_evidence),
            total_pages=total_pages,
            top_relevance=evidence_matches[0].relevance_score if evidence_matches else 0
        )
        
        search_time = time.time() - start_time
        
        result = SearchResult(
            total_pages_scanned=total_pages,
            pages_with_evidence=len(pages_with_evidence),
            evidence_pages=sorted(list(pages_with_evidence)),
            evidence_matches=evidence_matches,
            keywords_used=keywords,
            search_time_seconds=round(search_time, 2),
            confidence=confidence
        )
        
        print(f"      ✅ Scan complete: {len(pages_with_evidence)} pages with evidence")
        print(f"      ⏱️  Time: {search_time:.1f}s")
        
        return result
    
    # ========================================================================
    # KEYWORD EXTRACTION
    # ========================================================================
    
    def _extract_keywords(self, requirement: str) -> List[str]:
        """
        Extract search keywords from legal obligation
        
        Strategies:
        1. Domain pattern matching
        2. Quoted terms
        3. Capitalized entities
        4. Technical/financial terms
        5. Remove stop words
        
        Args:
            requirement: Legal obligation text
        
        Returns:
            List of search keywords
        """
        
        keywords = []
        req_lower = requirement.lower()
        
        # Strategy 1: Domain pattern matching
        for category, terms in self.domain_patterns.items():
            if any(term in req_lower for term in terms):
                keywords.extend(terms)
        
        # Strategy 2: Extract quoted terms (high priority)
        quoted = re.findall(r'"([^"]+)"', requirement)
        keywords.extend(quoted)
        
        # Strategy 3: Extract capitalized terms (entity names)
        capitalized = re.findall(
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',
            requirement
        )
        keywords.extend(capitalized)
        
        # Strategy 4: Technical/financial/compliance terms (expanded)
        technical_terms = re.findall(
            r'\b(?:EBITDA|EBIT|P&L|ROE|ROCE|ROIC|ROA|EPS|NAV|IPO|DRHP|'
            r'SEBI|ICDR|Companies Act|RoC|MCA|'
            r'revenue|profit|margin|debt|equity|disclosure|'
            r'subsidiary|associate|promoter|director|KMP|'
            r'litigation|risk factor|material|'
            r'certification|ISO|patent|trademark)\b',
            requirement,
            re.IGNORECASE
        )
        keywords.extend(technical_terms)
        
        # Strategy 4a: Extract regulation/section numbers
        # Examples: "Regulation 403", "Section 203", "Schedule III"
        regulation_refs = re.findall(
            r'\b(?:Regulation|Section|Rule|Schedule|Chapter|Clause)\s+[IVX0-9]+[A-Za-z]?\b',
            requirement,
            re.IGNORECASE
        )
        keywords.extend(regulation_refs)
        
        # Strategy 4b: Extract financial amounts and percentages (for context)
        amounts = re.findall(
            r'₹\s*[\d,]+(?:\.\d+)?(?:\s*(?:crore|lakh|million))?',
            requirement,
            re.IGNORECASE
        )
        keywords.extend(amounts[:3])  # Limit to 3 amounts
        
        # Strategy 5: Extract important words (>3 chars, not stop words)
        stop_words = {
            'the', 'and', 'for', 'with', 'this', 'that', 'from',
            'have', 'has', 'been', 'were', 'are', 'was', 'will',
            'shall', 'should', 'must', 'may', 'can', 'any', 'all'
        }
        
        words = re.findall(r'\b[a-zA-Z]{4,}\b', requirement.lower())
        keywords.extend([w for w in words if w not in stop_words])
        
        # Remove duplicates, preserve order
        seen = set()
        unique_keywords = []
        for kw in keywords:
            kw_lower = kw.lower()
            if kw_lower not in seen and len(kw) > 2:
                seen.add(kw_lower)
                unique_keywords.append(kw)
        
        return unique_keywords[:30]  # Top 30 keywords
    
    # ========================================================================
    # PAGE-LEVEL MATCHING
    # ========================================================================
    
    def _find_matches_on_page(
        self,
        page_num: int,
        page_text: str,
        keywords: List[str],
        requirement: str
    ) -> EvidenceMatch:
        """
        Find evidence matches on a single page
        
        Args:
            page_num: Page number
            page_text: Full text of page
            keywords: Search keywords
            requirement: Original requirement
        
        Returns:
            EvidenceMatch object (may have 0 relevance if no matches)
        """
        
        if not page_text or len(page_text.strip()) < 50:
            # Skip nearly empty pages
            return None
        
        page_lower = page_text.lower()
        
        # Find keyword matches with importance tracking
        matched_keywords = []
        important_matches = []  # Track high-value keywords
        
        # Classify keywords by importance
        important_terms = {
            'regulation', 'section', 'schedule', 'mandatory', 'material',
            'disclosure', 'ebitda', 'revenue', 'profit', 'subsidiary',
            'director', 'promoter', 'litigation', 'risk factor'
        }
        
        for kw in keywords:
            if kw.lower() in page_lower:
                matched_keywords.append(kw)
                if any(imp in kw.lower() for imp in important_terms):
                    important_matches.append(kw)
        
        if not matched_keywords:
            return None  # No matches on this page
        
        # Calculate base relevance score
        base_relevance = len(matched_keywords) / max(len(keywords), 1)
        
        # Apply importance weighting
        importance_boost = len(important_matches) * 0.15
        relevance = min(base_relevance + importance_boost, 1.0)
        
        # Boost score if multiple keywords appear together (proximity bonus)
        if len(matched_keywords) >= 3:
            # Check if keywords appear within 200 characters of each other
            keyword_positions = []
            for kw in matched_keywords[:5]:
                pos = page_lower.find(kw.lower())
                if pos >= 0:
                    keyword_positions.append(pos)
            
            if len(keyword_positions) >= 3:
                keyword_positions.sort()
                if keyword_positions[-1] - keyword_positions[0] < 200:
                    relevance *= 1.3  # Strong proximity bonus
        
        # Exact phrase match bonus
        # Check if requirement contains long phrases that match exactly
        requirement_phrases = re.findall(r'\b\w+\s+\w+\s+\w+\b', requirement.lower())
        for phrase in requirement_phrases[:3]:
            if phrase in page_lower:
                relevance *= 1.2
                break
        
        # Extract relevant context
        context_sentences = self._extract_context_sentences(
            page_text, matched_keywords
        )
        
        if not context_sentences:
            return None
        
        # Create text snippet (first relevant sentence)
        snippet = context_sentences[0] if context_sentences else ""
        if len(snippet) > 300:
            snippet = snippet[:300] + "..."
        
        return EvidenceMatch(
            page_number=page_num,
            text_snippet=snippet,
            keyword_matches=matched_keywords,
            relevance_score=min(relevance, 1.0),  # Cap at 1.0
            context_sentences=context_sentences[:5]  # Top 5 sentences
        )
    
    def _extract_context_sentences(
        self,
        page_text: str,
        keywords: List[str]
    ) -> List[str]:
        """
        Extract sentences containing keywords
        
        Enhanced to capture fuller context for complex requirements
        
        Args:
            page_text: Full page text
            keywords: Matched keywords
        
        Returns:
            List of relevant sentences
        """
        
        # Split into sentences (handle common abbreviations)
        text = page_text.replace('Dr.', 'Dr').replace('Mr.', 'Mr').replace('Mrs.', 'Mrs')
        text = text.replace('Ltd.', 'Ltd').replace('Inc.', 'Inc').replace('Pvt.', 'Pvt')
        text = text.replace('Co.', 'Co').replace('Nos.', 'Nos').replace('viz.', 'viz')
        
        sentences = re.split(r'[.!?]+', text)
        
        relevant = []
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            
            if len(sentence) < 20:  # Skip fragments
                continue
            
            # Check if sentence contains any keyword
            sentence_lower = sentence.lower()
            matching_keywords = [kw for kw in keywords if kw.lower() in sentence_lower]
            
            if matching_keywords:
                # For complex requirements, include neighboring sentences for context
                context = sentence
                
                # Add previous sentence if exists and relevant
                if i > 0 and len(matching_keywords) >= 2:
                    prev_sentence = sentences[i-1].strip()
                    if len(prev_sentence) >= 20:
                        context = prev_sentence + ". " + context
                
                # Add next sentence if exists and contains numbers/data
                if i < len(sentences) - 1 and len(matching_keywords) >= 2:
                    next_sentence = sentences[i+1].strip()
                    if len(next_sentence) >= 20 and re.search(r'\d', next_sentence):
                        context = context + ". " + next_sentence
                
                relevant.append(context)
        
        # Sort by keyword density (number of keywords per sentence)
        def keyword_density(sent):
            sent_lower = sent.lower()
            count = sum(1 for kw in keywords if kw.lower() in sent_lower)
            # Bonus for numbers (often contains specific data)
            if re.search(r'₹|%|\d+(?:,\d+)*(?:\.\d+)?', sent):
                count += 1
            return count
        
        relevant.sort(key=keyword_density, reverse=True)
        
        return relevant
    
    # ========================================================================
    # CONFIDENCE CALCULATION
    # ========================================================================
    
    def _calculate_confidence(
        self,
        pages_with_evidence: int,
        total_pages: int,
        top_relevance: float
    ) -> str:
        """
        Calculate search confidence level
        
        Args:
            pages_with_evidence: Number of pages with matches
            total_pages: Total pages scanned
            top_relevance: Highest relevance score
        
        Returns:
            'high', 'medium', or 'low'
        """
        
        if pages_with_evidence == 0:
            # No evidence found after scanning ALL pages
            return 'high'  # High confidence it's MISSING
        
        coverage = pages_with_evidence / max(total_pages, 1)
        
        # High confidence if:
        # - Multiple pages with evidence (3+)
        # - OR single page with high relevance (>0.7)
        # - OR good coverage (>2% of document)
        if (pages_with_evidence >= 3 or 
            top_relevance > 0.7 or 
            coverage > 0.02):
            return 'high'
        
        # Medium confidence if:
        # - 1-2 pages with evidence
        # - Relevance > 0.4
        if pages_with_evidence >= 1 and top_relevance > 0.4:
            return 'medium'
        
        return 'low'
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def format_results_summary(self, result: SearchResult) -> str:
        """Format search results as text summary"""
        
        lines = [
            f"EXHAUSTIVE SEARCH RESULTS:",
            f"- Total pages scanned: {result.total_pages_scanned}",
            f"- Pages with evidence: {result.pages_with_evidence}",
            f"- Evidence pages: {result.evidence_pages[:10]}",
            f"- Keywords used: {', '.join(result.keywords_used[:10])}",
            f"- Search time: {result.search_time_seconds}s",
            f"- Confidence: {result.confidence.upper()}",
            ""
        ]
        
        if result.evidence_matches:
            lines.append("TOP EVIDENCE MATCHES:")
            for i, match in enumerate(result.evidence_matches[:5], 1):
                lines.append(f"\n{i}. Page {match.page_number} (Relevance: {match.relevance_score:.0%})")
                lines.append(f"   Keywords: {', '.join(match.keyword_matches[:5])}")
                lines.append(f"   Text: {match.text_snippet}")
        else:
            lines.append("NO EVIDENCE FOUND ACROSS ENTIRE DOCUMENT")
        
        return '\n'.join(lines)
    
    def get_evidence_for_llm(
        self,
        result: SearchResult,
        max_pages: int = 15
    ) -> str:
        """
        Format evidence for LLM prompt
        
        Args:
            result: SearchResult from exhaustive search
            max_pages: Maximum pages to include
        
        Returns:
            Formatted evidence text
        """
        
        if not result.evidence_matches:
            return "NO EVIDENCE FOUND after scanning all pages."
        
        evidence_text = f"EVIDENCE FROM {result.pages_with_evidence} PAGES:\n\n"
        
        for match in result.evidence_matches[:max_pages]:
            evidence_text += f"[Page {match.page_number} - Relevance: {match.relevance_score:.0%}]\n"
            evidence_text += f"Matched: {', '.join(match.keyword_matches[:5])}\n"
            
            # Include all context sentences
            for sentence in match.context_sentences:
                evidence_text += f"{sentence}\n"
            
            evidence_text += "\n"
        
        return evidence_text


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def get_exhaustive_search_engine():
    """Factory function to create search engine"""
    return ExhaustiveSearchEngine()


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """Test the exhaustive search engine"""
    
    print("="*80)
    print("🧪 TESTING EXHAUSTIVE SEARCH ENGINE")
    print("="*80)
    
    # Mock pages dict
    mock_pages = {
        1: "Draft Red Herring Prospectus. Cover Page. Company XYZ Limited.",
        2: "Table of Contents. Business Overview... Risk Factors...",
        3: "Disclaimer. Forward looking statements...",
        47: "Research and Development. The Company operates two R&D facilities in Bangalore and Pune. R&D expenditure was ₹5.2 crore in FY2024, representing 2.1% of revenue.",
        48: "The R&D team consists of 45 engineers focused on product innovation and development.",
        142: "The Company has developed proprietary technology for manufacturing efficiency."
    }
    
    # Create engine
    engine = ExhaustiveSearchEngine()
    
    # Test search
    result = engine.search_entire_document(
        pages_dict=mock_pages,
        requirement="Disclose details of R&D facilities and expenditure"
    )
    
    # Print results
    print("\n" + engine.format_results_summary(result))
    
    print("\n" + "="*80)
    print("✅ TEST COMPLETE")
    print("="*80)