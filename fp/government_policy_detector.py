"""
Government Policy & Incentive Detector - FIXES MISS #2
=======================================================
Detects when company operates in sectors with government schemes
but doesn't disclose policy benefits/incentives.

This fixes the "Government policies for toys & foam" type misses.

Author: IPO Compliance System - Accuracy Enhancement
Date: January 2026
"""

import re
from typing import Dict, List, Set


class GovernmentPolicyDetector:
    """
    Detects industry sectors with government schemes
    and generates queries for policy disclosure
    
    Catches:
    - PLI schemes
    - Make in India benefits
    - Export incentives
    - Tax holidays
    - Subsidies
    """
    
    def __init__(self):
        """Initialize policy detector"""
        
        # Sectors with major government schemes
        self.policy_sectors = {
            'toys': {
                'keywords': ['toy', 'toys', 'plaything', 'educational toy', 'soft toy'],
                'schemes': ['National Action Plan for Toys (NAPT)', 'PLI Scheme for toys', 'Quality Control Orders for toys']
            },
            'foam': {
                'keywords': ['foam', 'polyurethane', 'pu foam', 'mattress', 'cushioning'],
                'schemes': ['PLI for Textiles (foam products)', 'Production incentives']
            },
            'defense': {
                'keywords': ['defense', 'defence', 'aerospace', 'weapon', 'ordnance', 'military'],
                'schemes': ['Defense Production Policy', 'iDEX', 'PLI for Drone Components', 'Make in India in Defense']
            },
            'renewable_energy': {
                'keywords': ['solar', 'wind', 'renewable', 'energy storage', 'photovoltaic', 'green energy'],
                'schemes': ['PLI for Solar PV Modules', 'National Green Hydrogen Mission', 'FAME-II (EV Charging)']
            },
            'it_saas': {
                'keywords': ['software', 'saas', 'cloud', 'digital', 'it services', 'coding'],
                'schemes': ['STPI Schemes', 'SEIS (Service Exports from India)', 'MeitY Startup Hub']
            },
            'furniture': {
                'keywords': ['furniture', 'woodworking', 'office furniture', 'modular furniture'],
                'schemes': ['Furniture Cluster Scheme', 'Export Promotion for Furniture']
            },
            'electronics': {
                'keywords': ['electronics', 'semiconductor', 'mobile', 'led', 'hardware'],
                'schemes': ['PLI for Electronics', 'EMC 2.0', 'SPECS scheme']
            },
            'pharma': {
                'keywords': ['pharmaceutical', 'pharma', 'drug', 'api', 'medical device'],
                'schemes': ['PLI for Pharmaceuticals', 'PLI for Medical Devices', 'Promotion of Bulk Drug Parks']
            },
            'textiles': {
                'keywords': ['textile', 'fabric', 'garment', 'apparel', 'yarn'],
                'schemes': ['PLI for Textiles', 'PM MITRA', 'RoDTEP Scheme']
            }
        }
        
        # General policy indicators
        self.policy_keywords = [
            'pli', 'production linked incentive', 'make in india',
            'atmanirbhar', 'subsidy', 'incentive', 'export promotion',
            'duty drawback', 'meis', 'seis', 'rodtep',
            'tax holiday', 'concessional', 'government scheme'
        ]
        
        print("✅ Government Policy Detector initialized")
    
    def detect_policy_gaps(
        self, 
        pages_dict: Dict[int, str],
        company_profile: Dict
    ) -> List[Dict]:
        """
        Detect if company is in policy-eligible sector but missing disclosure
        
        Args:
            pages_dict: {page_num: page_text}
            company_profile: Company business type
        
        Returns:
            List of policy disclosure queries
        """
        
        queries = []
        
        # Identify company's sectors
        identified_sectors = self._identify_sectors(pages_dict, company_profile)
        
        if not identified_sectors:
            return []  # No policy-eligible sectors found
        
        # Check if policy benefits are disclosed
        has_policy_disclosure = self._has_policy_disclosure(pages_dict)
        
        if not has_policy_disclosure:
            # Generate query for each identified sector
            for sector in identified_sectors:
                query = self._generate_policy_query(sector, pages_dict)
                queries.append(query)
        
        return queries
    
    def _identify_sectors(
        self, 
        pages_dict: Dict[int, str],
        company_profile: Dict
    ) -> Set[str]:
        """Identify which policy-eligible sectors company operates in"""
        
        identified = set()
        
        # Combine all text
        all_text = " ".join(pages_dict.values()).lower()
        
        # Check each sector
        for sector, data in self.policy_sectors.items():
            keywords = data['keywords']
            
            # Count keyword mentions
            mentions = sum(1 for kw in keywords if kw in all_text)
            
            # Need at least 3 mentions to confirm sector
            if mentions >= 3:
                identified.add(sector)
        
        # Also check company profile
        business_type = company_profile.get('business_type', '').lower()
        for sector, data in self.policy_sectors.items():
            if any(kw in business_type for kw in data['keywords']):
                identified.add(sector)
        
        return identified
    
    def _has_policy_disclosure(self, pages_dict: Dict[int, str]) -> bool:
        """Check if document already discloses government policies/benefits"""
        
        all_text = " ".join(pages_dict.values()).lower()
        
        # Look for policy disclosure patterns
        policy_disclosure_patterns = [
            r'government\s+(?:scheme|policy|incentive|benefit)',
            r'pli\s+scheme',
            r'production\s+linked\s+incentive',
            r'eligible\s+for.*?(?:scheme|incentive)',
            r'availed.*?(?:benefit|incentive|subsidy)',
            r'under\s+(?:the\s+)?(?:scheme|policy)'
        ]
        
        matches = sum(
            1 for pattern in policy_disclosure_patterns
            if re.search(pattern, all_text)
        )
        
        # Need at least 2 mentions to consider disclosed
        return matches >= 2
    
    def _generate_policy_query(
        self, 
        sector: str,
        pages_dict: Dict[int, str]
    ) -> Dict:
        """Generate NSE-style policy disclosure query"""
        
        sector_data = self.policy_sectors[sector]
        schemes_list = ", ".join(sector_data['schemes'])
        
        # Find a relevant page (where sector is mentioned)
        relevant_page = self._find_relevant_page(sector, pages_dict)
        
        query_text = (
            f"The Company operates in the {sector} sector which is covered under "
            f"various government schemes including {schemes_list}. "
            f"Kindly specify the applicability of these schemes to the Company's "
            f"operations and provide details of benefits availed or expected to be "
            f"availed. If not applicable, provide rationale. "
            f"Provide revised draft along with confirmation that the same shall be "
            f"updated in the prospectus."
        )
        
        return {
            'page': str(relevant_page),
            'text': query_text,
            'type': 'TYPE_POLICY_DISCLOSURE',
            'issue_id': f'GOVT_POLICY_{sector.upper()}',
            'severity': 'Material',
            'category': 'Regulatory'
        }
    
    def _find_relevant_page(
        self, 
        sector: str, 
        pages_dict: Dict[int, str]
    ) -> int:
        """Find page where sector is most mentioned"""
        
        keywords = self.policy_sectors[sector]['keywords']
        
        page_scores = {}
        for page_num, text in pages_dict.items():
            text_lower = text.lower()
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                page_scores[page_num] = score
        
        if page_scores:
            return max(page_scores, key=page_scores.get)
        else:
            return list(pages_dict.keys())[0]  # Fallback to first page


def get_government_policy_detector():
    """Factory function"""
    return GovernmentPolicyDetector()


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """Test the detector"""
    
    detector = GovernmentPolicyDetector()
    
    # Test text
    test_text = """
    The Company is engaged in manufacturing of toys and foam products.
    Our toy manufacturing facility produces educational toys and playthings.
    We also manufacture polyurethane foam for the automotive sector.
    """
    
    pages_dict = {10: test_text}
    company_profile = {'business_type': 'manufacturing'}
    
    queries = detector.detect_policy_gaps(pages_dict, company_profile)
    
    print(f"\n🔍 Found {len(queries)} policy queries:")
    for q in queries:
        print(f"\n{q['text']}")