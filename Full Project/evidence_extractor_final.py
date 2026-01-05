"""
Evidence Extractor - Complete Version
======================================
Extracts verbatim quotes, figures, names, and detects inconsistencies
for NSE-style compliance query generation.

Features:
1. Verbatim text extraction from specific pages
2. Monetary amounts and percentages extraction
3. Person names extraction
4. Cross-page consistency checking
5. Smart snippet selection
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict


class EvidenceExtractor:
    """
    Complete evidence extraction for compliance queries
    """
    
    def __init__(self):
        """Initialize Evidence Extractor"""
        self.stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 
            'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 'are',
            'was', 'were', 'been', 'being', 'have', 'has', 'had', 'do',
            'does', 'did', 'will', 'would', 'should', 'could', 'may',
            'might', 'must', 'can', 'shall'
        }
    
    def extract_from_pages(
        self,
        pages: List[int],
        drhp_chunks: List[Dict[str, Any]],
        search_terms: Optional[List[str]] = None,
        max_length: int = 400
    ) -> Dict[str, Any]:
        """
        Extract evidence from specific pages
        
        Args:
            pages: List of page numbers
            drhp_chunks: Document chunks
            search_terms: Keywords to highlight
            max_length: Max snippet length
        
        Returns:
            Extracted evidence with context
        """
        
        if not pages or not drhp_chunks:
            return {
                'verbatim_text': '',
                'full_text': '',
                'pages': [],
                'context_available': False
            }
        
        # Get text from specified pages
        page_texts = {}
        for chunk in drhp_chunks:
            chunk_page = chunk.get('page_number') or chunk.get('page', 0)
            if chunk_page in pages:
                if chunk_page not in page_texts:
                    page_texts[chunk_page] = []
                page_texts[chunk_page].append(chunk.get('text', ''))
        
        if not page_texts:
            return {
                'verbatim_text': '',
                'full_text': '',
                'pages': pages,
                'context_available': False
            }
        
        # Combine text from all pages
        combined_text = ""
        for page_num in sorted(page_texts.keys()):
            page_content = " ".join(page_texts[page_num])
            combined_text += f"{page_content}\n\n"
        
        # If search terms provided, extract relevant snippet
        if search_terms:
            best_snippet = self.find_best_snippet(
                text=combined_text,
                search_terms=search_terms,
                max_length=max_length
            )
        else:
            # Take first max_length characters
            best_snippet = combined_text[:max_length]
            if len(combined_text) > max_length:
                best_snippet += "..."
        
        return {
            'verbatim_text': best_snippet.strip(),
            'full_text': combined_text,
            'pages': sorted(page_texts.keys()),
            'context_available': True,
            'total_length': len(combined_text)
        }
    
    def find_best_snippet(
        self,
        text: str,
        search_terms: List[str],
        max_length: int = 400
    ) -> str:
        """
        Find best text snippet containing search terms
        """
        
        terms = [t.lower() for t in search_terms if t]
        if not terms:
            snippet = text[:max_length]
            return snippet + ("..." if len(text) > max_length else "")
        
        # Find all term positions
        text_lower = text.lower()
        term_positions = []
        
        for term in terms:
            pos = 0
            while True:
                pos = text_lower.find(term, pos)
                if pos == -1:
                    break
                term_positions.append(pos)
                pos += 1
        
        if not term_positions:
            snippet = text[:max_length]
            return snippet + ("..." if len(text) > max_length else "")
        
        # Find center point
        center = sorted(term_positions)[len(term_positions) // 2]
        
        # Extract snippet around center
        start = max(0, center - max_length // 2)
        end = min(len(text), center + max_length // 2)
        
        snippet = text[start:end]
        
        # Add ellipsis
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."
        
        return snippet.strip()
    
    def extract_figures_and_amounts(
        self,
        text: str
    ) -> List[Dict[str, Any]]:
        """
        Extract monetary amounts with context
        
        Returns:
            List of dicts with 'amount', 'context', 'position'
        """
        
        # Pattern for Indian currency
        amount_pattern = r'₹\s*[\d,]+\.?\d*\s*(?:lakhs?|lakh|crores?|crore|million|billion)?'
        
        amounts = []
        for match in re.finditer(amount_pattern, text, re.IGNORECASE):
            amount_text = match.group(0)
            pos = match.start()
            
            # Get context (30 chars before and after)
            context_start = max(0, pos - 30)
            context_end = min(len(text), pos + len(amount_text) + 30)
            context = text[context_start:context_end]
            
            amounts.append({
                'amount': amount_text.strip(),
                'context': context.strip(),
                'position': pos
            })
        
        # Also extract percentages
        percentage_pattern = r'\d+\.?\d*\s*%'
        for match in re.finditer(percentage_pattern, text):
            pct_text = match.group(0)
            pos = match.start()
            
            context_start = max(0, pos - 30)
            context_end = min(len(text), pos + len(pct_text) + 30)
            context = text[context_start:context_end]
            
            amounts.append({
                'amount': pct_text.strip(),
                'context': context.strip(),
                'position': pos
            })
        
        return amounts
    
    def extract_names(
        self,
        text: str
    ) -> List[Dict[str, Any]]:
        """
        Extract person names with titles
        
        Returns:
            List of dicts with 'name', 'context', 'position'
        """
        
        # Pattern for formal names
        name_pattern = r'(?:Mr\.|Ms\.|Dr\.|Mrs\.|Shri|Smt\.)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+'
        
        names = []
        for match in re.finditer(name_pattern, text):
            name_text = match.group(0)
            pos = match.start()
            
            # Get context
            context_start = max(0, pos - 40)
            context_end = min(len(text), pos + len(name_text) + 40)
            context = text[context_start:context_end]
            
            names.append({
                'name': name_text.strip(),
                'context': context.strip(),
                'position': pos
            })
        
        return names
    
    def extract_keywords(
        self,
        text: str,
        top_n: int = 10
    ) -> List[str]:
        """Extract key terms from text"""
        
        # Split and clean
        words = re.findall(r'\b[A-Za-z]{3,}\b', text.lower())
        keywords = [w for w in words if w not in self.stopwords]
        
        # Get unique, keep order
        seen = set()
        unique_keywords = []
        for k in keywords:
            if k not in seen:
                seen.add(k)
                unique_keywords.append(k)
        
        return unique_keywords[:top_n]
    
    def check_cross_page_consistency(
        self,
        drhp_chunks: List[Dict[str, Any]],
        page_range: Optional[Tuple[int, int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Check for inconsistencies across pages
        
        Args:
            drhp_chunks: All document chunks
            page_range: Optional (start_page, end_page) to limit check
        
        Returns:
            List of inconsistencies found
        """
        
        inconsistencies = []
        
        # Group chunks by page
        pages_data = defaultdict(str)
        for chunk in drhp_chunks:
            page = chunk.get('page_number') or chunk.get('page', 0)
            if page_range:
                if page < page_range[0] or page > page_range[1]:
                    continue
            pages_data[page] += chunk.get('text', '') + " "
        
        if len(pages_data) < 2:
            return []
        
        # Extract all amounts from all pages
        page_amounts = {}
        for page, text in pages_data.items():
            amounts = self.extract_figures_and_amounts(text)
            page_amounts[page] = amounts
        
        # Compare amounts across pages
        all_amount_values = defaultdict(list)  # amount_value -> [(page, context)]
        
        for page, amounts in page_amounts.items():
            for amt in amounts:
                # Normalize amount for comparison
                normalized = self.normalize_amount(amt['amount'])
                if normalized:
                    all_amount_values[normalized].append((page, amt['context']))
        
        # Find conflicting amounts (same metric, different values)
        for amount_val, occurrences in all_amount_values.items():
            if len(occurrences) > 1:
                # Check if contexts are similar (might be same data point)
                contexts = [occ[1].lower() for occ in occurrences]
                
                # Simple heuristic: if contexts share 3+ words, might be inconsistency
                for i in range(len(contexts)):
                    for j in range(i + 1, len(contexts)):
                        words_i = set(re.findall(r'\b\w{4,}\b', contexts[i]))
                        words_j = set(re.findall(r'\b\w{4,}\b', contexts[j]))
                        
                        common_words = words_i & words_j
                        if len(common_words) >= 3:
                            # Potential inconsistency
                            inconsistencies.append({
                                'type': 'AMOUNT_CONFLICT',
                                'amount': amount_val,
                                'pages': [occurrences[i][0], occurrences[j][0]],
                                'contexts': [occurrences[i][1], occurrences[j][1]],
                                'severity': 'MEDIUM'
                            })
        
        return inconsistencies
    
    def normalize_amount(self, amount_str: str) -> Optional[float]:
        """
        Normalize amount string to float for comparison
        
        Examples:
            "₹125.50 crores" -> 1255000000.0
            "₹31.97 lakhs" -> 3197000.0
        """
        
        try:
            # Remove currency symbol and spaces
            cleaned = amount_str.replace('₹', '').replace(',', '').strip()
            
            # Extract number
            num_match = re.search(r'[\d.]+', cleaned)
            if not num_match:
                return None
            
            num = float(num_match.group(0))
            
            # Apply multiplier
            cleaned_lower = cleaned.lower()
            if 'crore' in cleaned_lower:
                return num * 10000000
            elif 'lakh' in cleaned_lower:
                return num * 100000
            elif 'million' in cleaned_lower:
                return num * 1000000
            elif 'billion' in cleaned_lower:
                return num * 1000000000
            else:
                return num
        except:
            return None
    
    def extract_context_for_query(
        self,
        compliance_result: Dict[str, Any],
        drhp_chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Extract comprehensive context for query generation
        
        Returns:
            Complete evidence package with all extracted data
        """
        
        pages = compliance_result.get('pages', [])
        evidence = compliance_result.get('evidence', '')
        obligation = compliance_result.get('obligation', '')
        
        # Extract keywords from obligation
        keywords = self.extract_keywords(obligation)
        
        # Get verbatim text from pages
        evidence_data = self.extract_from_pages(
            pages=pages,
            drhp_chunks=drhp_chunks,
            search_terms=keywords,
            max_length=500
        )
        
        # Extract figures and names
        if evidence_data['context_available']:
            full_text = evidence_data['full_text']
            figures = self.extract_figures_and_amounts(full_text)
            names = self.extract_names(full_text)
        else:
            figures = []
            names = []
        
        # Check for cross-page inconsistencies
        if len(pages) > 1:
            inconsistencies = self.check_cross_page_consistency(
                drhp_chunks=drhp_chunks,
                page_range=(min(pages), max(pages))
            )
        else:
            inconsistencies = []
        
        return {
            'verbatim_quote': evidence_data['verbatim_text'],
            'full_text': evidence_data.get('full_text', ''),
            'pages': evidence_data['pages'],
            'context_available': evidence_data['context_available'],
            'figures_found': [f['amount'] for f in figures[:5]],
            'figures_with_context': figures[:5],
            'names_found': [n['name'] for n in names[:5]],
            'names_with_context': names[:5],
            'keywords': keywords,
            'original_evidence': evidence,
            'inconsistencies': inconsistencies
        }


def get_evidence_extractor():
    """Factory function"""
    return EvidenceExtractor()


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """Test Evidence Extractor"""
    
    print("="*80)
    print("🧪 TESTING ENHANCED EVIDENCE EXTRACTOR")
    print("="*80)
    
    # Mock data
    mock_chunks = [
        {
            'page': 145,
            'page_number': 145,
            'text': 'Eco Fuel Systems (India) Limited. Revenue for FY2024 was ₹125.50 crores.'
        },
        {
            'page': 146,
            'page_number': 146,
            'text': 'Mr. Vijay Patel - MD (DIN: 12345678). Ms. Priya Shah - CFO. Total revenue ₹125.50 crores.'
        },
        {
            'page': 147,
            'page_number': 147,
            'text': 'Revenue from operations: ₹125.5 crores in FY2024. EBITDA margin: 15.8%.'
        }
    ]
    
    extractor = EvidenceExtractor()
    
    # Test 1: Basic extraction
    print("\n" + "="*80)
    print("TEST 1: Verbatim Evidence Extraction")
    print("="*80)
    
    evidence = extractor.extract_from_pages([146], mock_chunks, ['director', 'DIN'])
    print(f"Verbatim: {evidence['verbatim_text'][:100]}...")
    
    # Test 2: Figures extraction
    print("\n" + "="*80)
    print("TEST 2: Figures Extraction")
    print("="*80)
    
    figures = extractor.extract_figures_and_amounts(evidence['full_text'])
    print(f"Found {len(figures)} figures:")
    for fig in figures:
        print(f"  - {fig['amount']}: {fig['context'][:50]}...")
    
    # Test 3: Cross-page consistency
    print("\n" + "="*80)
    print("TEST 3: Cross-Page Consistency Check")
    print("="*80)
    
    inconsistencies = extractor.check_cross_page_consistency(mock_chunks)
    print(f"Found {len(inconsistencies)} inconsistencies")
    for inc in inconsistencies:
        print(f"  - {inc['type']} on pages {inc['pages']}")
    
    print("\n" + "="*80)
    print("✅ All Tests Complete!")
    print("="*80)
