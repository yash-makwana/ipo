"""
NSE Engine Adapter - Production Grade
======================================
Bridges SystemB's 4-engine pipeline into SystemA's multi-agent orchestrator.

This adapter:
1. Takes DRHP chunks from SystemA's document processor
2. Runs SystemB's Engine 1 (doc intel) for page extraction
3. Runs SystemB's Engine 3 (content review) for NSE queries
4. Runs SystemB's Engine 4 (formatter) for output
5. Returns NSE queries in SystemA's expected format
"""

import sys
import os
from typing import List, Dict, Any, Optional

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engines.engine_1_doc_intel import DocumentIntelligenceEngine
from engines.engine_3_content_review import ContentReviewEngine
from engines.engine_4_formatter import NSEOutputFormatter
from data.icdr_regulation_mapper import add_regulation_to_query, get_regulation_reference


class NSEEngineAdapter:
    """
    Adapter that wraps SystemB's engines for use in SystemA's orchestrator
    
    Features:
    - Superior page number extraction (solves "page 0" issue)
    - Checklist-driven NSE query generation (75% accuracy)
    - Proper ICDR regulation references
    - NSE-style output formatting
    """
    
    def __init__(self):
        """Initialize the NSE Engine Adapter"""
        self.name = "NSE Engine Adapter (SystemB Integration)"
        # Tracks whether Engine 3 used Gemini on the last analyze call
        self.last_gemini_enabled = False
        print(f"✅ {self.name} initialized")
    
    def analyze_business_chapter(
        self,
        drhp_chunks: List[Dict[str, Any]],
        company_name: str = "the Company",
        company_profile: Optional[Dict[str, Any]] = None,
        pdf_path: Optional[str] = None,
        chapter_name: str = "Business Overview"
    ) -> List[Dict[str, Any]]:
        """
        Main method called by multi_agent_orchestrator.py
        
        This is the drop-in replacement for nse_content_review_agent_production.py
        
        Args:
            drhp_chunks: Document chunks from SystemA's processor
            company_name: Company name
            company_profile: {revenue, employees, business_type}
            pdf_path: Path to original PDF file (for Engine 1)
            chapter_name: Target chapter name
            
        Returns:
            List of NSE query dictionaries matching SystemA's format
        """
        
        print(f"\n{'='*80}")
        print(f"📋 NSE ENGINE ADAPTER - SYSTEMB INTEGRATION")
        print(f"{'='*80}")
        print(f"Company: {company_name}")
        print(f"Chapter: {chapter_name}")
        print(f"Chunks: {len(drhp_chunks)}")
        
        # ================================================================
        # PHASE 1: Document Intelligence (Engine 1)
        # ================================================================
        # If we have the PDF path, use Engine 1 for superior page extraction
        # Otherwise, reconstruct from chunks
        
        if pdf_path and os.path.exists(pdf_path):
            print(f"\n[Engine 1] Processing PDF with superior page extraction...")
            doc_engine = DocumentIntelligenceEngine(pdf_path)
            doc_data = doc_engine.process()
            pages_dict = doc_data['pages']
            print(f"[Engine 1] ✅ Extracted {len(pages_dict)} pages with accurate page numbers")
        else:
            print(f"\n[Engine 1] No PDF path provided, reconstructing from chunks...")
            pages_dict = self._reconstruct_pages_from_chunks(drhp_chunks)
            print(f"[Engine 1] ⚠️  Reconstructed {len(pages_dict)} pages (may have page number issues)")
        
        # ================================================================
        # PHASE 2: Content Review (Engine 3)
        # ================================================================
        print(f"\n[Engine 3] Running NSE Content Review (checklist-driven)...")
        
        review_engine = ContentReviewEngine(
            doc_data={'pages': pages_dict, 'tables': {}, 'metadata': {}},
            chapter_name=chapter_name
        )
        # Record whether the Gemini AI layer was enabled in this run
        try:
            self.last_gemini_enabled = bool(getattr(review_engine, 'gemini', None) and getattr(review_engine.gemini, 'enabled', False))
            print(f"[Engine 3] Gemini enabled: {self.last_gemini_enabled}")
        except Exception:
            self.last_gemini_enabled = False
        
        # Generate queries using SystemB's superior logic
        raw_queries = review_engine.generate_queries(pages_dict)
        
        print(f"[Engine 3] ✅ Generated {len(raw_queries)} NSE queries")
        
        # ================================================================
        # PHASE 3: Add ICDR Regulation References
        # ================================================================
        print(f"\n[ICDR Mapper] Adding regulation references...")
        
        enhanced_queries = []
        for query in raw_queries:
            # SystemB queries now have: page, text, type, issue_id, severity, category
            page = query.get('page', '—')
            observation_text = query.get('text', '')
            query_type = query.get('type', 'TYPE_DETERMINISTIC')
            
            # ✅ Use metadata from Engine 3 if available
            issue_id = query.get('issue_id', self._extract_issue_id(observation_text, query))
            severity = query.get('severity', self._determine_severity(observation_text, query_type))
            category = query.get('category', self._determine_category(issue_id))
            
            # Get regulation reference
            regulation_ref = get_regulation_reference(issue_id, severity)
            
            # Build enhanced query in SystemA's expected format
            enhanced_query = {
                'type': 'nse_content_query',
                'page': page,
                'observation': observation_text,
                'severity': severity,
                'category': category,
                'regulation_ref': regulation_ref,
                'missing_elements': [],  # SystemB doesn't track this separately
                'table_present': False,   # Could enhance later
                'issue_id': issue_id     # Keep for debugging
            }
            
            enhanced_queries.append(enhanced_query)
        
        print(f"[ICDR Mapper] ✅ Added regulation references to all queries")
        
        # ================================================================
        # PHASE 4: Return in SystemA format
        # ================================================================
        print(f"\n✅ NSE Engine Adapter completed successfully")
        print(f"   Total queries: {len(enhanced_queries)}")
        print(f"{'='*80}\n")
        
        return enhanced_queries
    
    def _reconstruct_pages_from_chunks(self, chunks: List[Dict[str, Any]]) -> Dict[int, str]:
        """
        Reconstruct page dictionary from chunks when PDF not available
        
        This is a fallback - Engine 1 with PDF is much better
        """
        pages_dict = {}
        
        for chunk in chunks:
            page = chunk.get('page_number') or chunk.get('page', 0)
            text = chunk.get('text', '')
            
            if page == 0:
                # Try to extract from metadata
                page = chunk.get('metadata', {}).get('page', 0)
            
            if page > 0:
                if page not in pages_dict:
                    pages_dict[page] = ""
                pages_dict[page] += text + "\n"
        
        return pages_dict
    
    def _determine_severity(self, observation_text: str, query_type: str) -> str:
        """
        Determine NSE severity level from query text and type
        
        Maps to: Major, Observation, Clarification, Critical
        """
        text_lower = observation_text.lower()
        
        # Critical indicators
        if any(word in text_lower for word in ['reconcile', 'contradiction', 'discrepancy', 'mismatch']):
            return 'Major'
        
        # Major indicators
        if any(word in text_lower for word in ['kindly provide', 'kindly disclose', 'kindly confirm']):
            return 'Major'
        
        # Observation indicators
        if 'kindly clarify' in text_lower or 'kindly elaborate' in text_lower:
            return 'Observation'
        
        # Type-based fallback
        if query_type in ['TYPE_CONTRADICTION', 'TYPE_MASTER']:
            return 'Major'
        elif query_type == 'TYPE_PROCEDURAL':
            return 'Observation'
        
        return 'Clarification'
    
    def _extract_issue_id(self, observation_text: str, query: Dict) -> str:
        """
        Extract issue_id from query for regulation mapping
        
        SystemB's Engine 3 should ideally pass this, but we can infer from text
        """
        text_lower = observation_text.lower()
        
        # Map keywords to issue IDs
        keyword_to_issue = {
            'revenue bifurcation': 'GEOGRAPHIC_REVENUE_SPLIT',
            'state-wise': 'GEOGRAPHIC_REVENUE_SPLIT',
            'attrition': 'ATTRITION_RATE',
            'superlative': 'SUPERLATIVE_EVIDENCE',
            'jargon': 'UNDEFINED_JARGON',
            'measurement unit': 'MEASUREMENT_UNIT_CONSISTENCY',
            'distributor': 'DISTRIBUTOR_HEALTH_DETAIL',
            'supplier': 'SUPPLIER_CONCENTRATION',
            'r&d': 'RD_INVESTMENT_DISCLOSURE',
            'csr': 'CSR_BUDGET_EXECUTION',
            'lease': 'LEASE_STATUS_MANDATORY',
            'related party': 'ARM_LENGTH_RPT_DISCLOSURE',
            'capacity': 'CAPACITY_CERTIFICATION',
            'insurance': 'INSURANCE_AUDIT_MISMATCH',
        }
        
        for keyword, issue_id in keyword_to_issue.items():
            if keyword in text_lower:
                return issue_id
        
        return 'GENERAL_DISCLOSURE'
    
    def _determine_category(self, issue_id: str) -> str:
        """Determine category from issue_id"""
        category_map = {
            'GEOGRAPHIC_REVENUE_SPLIT': 'Revenue Disclosure',
            'ATTRITION_RATE': 'Human Resources',
            'SUPERLATIVE_EVIDENCE': 'Forward-Looking Statements',
            'UNDEFINED_JARGON': 'Terminology',
            'MEASUREMENT_UNIT_CONSISTENCY': 'Data Consistency',
            'DISTRIBUTOR_HEALTH_DETAIL': 'Business Operations',
            'SUPPLIER_CONCENTRATION': 'Supply Chain',
            'RD_INVESTMENT_DISCLOSURE': 'R&D',
            'CSR_BUDGET_EXECUTION': 'Corporate Social Responsibility',
            'LEASE_STATUS_MANDATORY': 'Properties',
            'ARM_LENGTH_RPT_DISCLOSURE': 'Related Party Transactions',
            'CAPACITY_CERTIFICATION': 'Manufacturing',
            'INSURANCE_AUDIT_MISMATCH': 'Risk Management',
        }
        
        return category_map.get(issue_id, 'General Disclosure')


def get_nse_engine_adapter():
    """
    Factory function matching SystemA's convention
    
    This is the drop-in replacement for:
    from nse_content_review_agent_production import get_nse_content_review_agent
    """
    return NSEEngineAdapter()


# Backward compatibility alias
def get_nse_content_review_agent():
    """Alias for backward compatibility"""
    return get_nse_engine_adapter()
