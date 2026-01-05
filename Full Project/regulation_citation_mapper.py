"""
Regulation Citation Mapper
===========================
Maps generic regulation references to specific citations
for NSE-style queries.

Handles:
- ICDR Regulations (specific regulation numbers)
- Companies Act sections
- AIBI Compendium references
- Schedule references
"""

import re
from typing import Dict, Optional, List


class RegulationCitationMapper:
    """
    Maps regulations to specific citations
    """
    
    def __init__(self):
        """Initialize mapper with regulation patterns"""
        
        # ICDR Regulation mappings
        self.icdr_mappings = {
            'key managerial personnel': 'Regulation 403(b) and (c)',
            'kmp': 'Regulation 403(b) and (c)',
            'directors': 'Regulation 31, Schedule VIII',
            'board': 'Regulation 31, Schedule VIII',
            'financial information': 'Regulation 32, Schedule X',
            'financial statements': 'Regulation 32, Schedule X',
            'business overview': 'Regulation 32(2), Schedule XII',
            'risk factors': 'Regulation 18, Schedule X Part A',
            'objects of the issue': 'Regulation 4, 26',
            'capital structure': 'Regulation 32, Schedule XII',
            'shareholding': 'Regulation 31, 32',
            'promoter': 'Regulation 2(1)(oo), 31',
            'related party': 'Regulation 32, Schedule XII',
            'litigation': 'Regulation 32, Schedule XII Part A (8)',
            'material contracts': 'Regulation 32, Schedule XII',
            'government approvals': 'Regulation 32, Schedule XII',
            'tax benefits': 'Regulation 31, Schedule XII',
            'dividend': 'Regulation 32',
            'underwriting': 'Regulation 40-50',
            'listing': 'Regulation 28, 29',
            'allotment': 'Regulation 55-57',
        }
        
        # Companies Act mappings
        self.companies_act_mappings = {
            'directors': 'Section 149, 152',
            'board meetings': 'Section 173',
            'audit committee': 'Section 177',
            'related party transactions': 'Section 188',
            'loans': 'Section 185, 186',
            'deposit': 'Section 73-76',
            'dividend': 'Section 123, 124',
            'managerial remuneration': 'Section 197',
            'key managerial personnel': 'Section 203',
            'register of members': 'Section 88',
            'annual general meeting': 'Section 96',
            'financial statements': 'Section 129, 134',
            'statutory auditor': 'Section 139, 141',
            'corporate social responsibility': 'Section 135',
            'csr': 'Section 135',
        }
        
        # AIBI Compendium references
        self.aibi_mappings = {
            'top 10 customers': '[AIBI Compendium, Section: Complete Text, Page 6, Point 6]',
            'top 10 suppliers': '[AIBI Compendium, Section: Complete Text, Page 6, Point 7]',
            'production volume': '[AIBI Compendium, Section: Complete Text, Page 6, Point 9]',
            'sales volume': '[AIBI Compendium, Section: Complete Text, Page 6, Point 9]',
            'brand': '[AIBI Compendium, Section: Complete Text, Page 6, Point 13-14]',
            'expansion plans': '[AIBI Compendium, Section: Complete Text, Page 6, Point 15]',
            'government approvals': '[AIBI Compendium, Section: Complete Text, Page 28, Point 4]',
            'gst certificate': '[AIBI Compendium, Section: Complete Text]',
            'iso certification': '[AIBI Compendium, Section: Complete Text]',
            'data backup': '[AIBI Compendium, Section: Complete Text]',
        }
    
    def get_specific_citation(
        self,
        obligation: str,
        regulation_type: str,
        generic_citation: Optional[str] = None
    ) -> str:
        """
        Get specific citation for an obligation
        
        Args:
            obligation: The obligation text
            regulation_type: 'ICDR' or 'Companies Act'
            generic_citation: Current citation (if any)
        
        Returns:
            Specific citation string
        """
        
        obligation_lower = obligation.lower()
        
        # Check ICDR
        if regulation_type == "ICDR":
            for keyword, citation in self.icdr_mappings.items():
                if keyword in obligation_lower:
                    return citation
        
        # Check Companies Act
        elif regulation_type == "Companies Act" or regulation_type == "COMPANIES_ACT_2013":
            for keyword, citation in self.companies_act_mappings.items():
                if keyword in obligation_lower:
                    return f"Companies Act, 2013 - {citation}"
        
        # Check AIBI
        for keyword, citation in self.aibi_mappings.items():
            if keyword in obligation_lower:
                return citation
        
        # If we have a generic citation, try to parse it
        if generic_citation:
            parsed = self.parse_generic_citation(generic_citation)
            if parsed:
                return parsed
        
        # Fallback
        if regulation_type == "ICDR":
            return "SEBI (ICDR) Regulations, 2018"
        elif "Companies Act" in regulation_type or "COMPANIES_ACT" in regulation_type:
            return "Companies Act, 2013"
        else:
            return "Applicable Regulations"
    
    def parse_generic_citation(self, citation: str) -> Optional[str]:
        """
        Try to extract specific reference from generic citation
        
        Examples:
            "ICDR_2018_REG_403" -> "Regulation 403"
            "COMPANIES_ACT_SEC_203" -> "Section 203"
        """
        
        # Try to find regulation number
        reg_match = re.search(r'REG[_\s]*(\d+[a-z]*)', citation, re.IGNORECASE)
        if reg_match:
            return f"Regulation {reg_match.group(1)}"
        
        # Try to find section number
        sec_match = re.search(r'SEC[_\s]*(\d+)', citation, re.IGNORECASE)
        if sec_match:
            return f"Section {sec_match.group(1)}"
        
        # Try to find schedule
        sch_match = re.search(r'SCH[_\s]*(X+I*|[IVX]+|\d+)', citation, re.IGNORECASE)
        if sch_match:
            return f"Schedule {sch_match.group(1)}"
        
        return None
    
    def enhance_citation(
        self,
        base_citation: str,
        obligation: str
    ) -> str:
        """
        Enhance an existing citation with more details
        
        Args:
            base_citation: Current citation
            obligation: Obligation text
        
        Returns:
            Enhanced citation
        """
        
        if not base_citation or base_citation == "General Requirement":
            return self.get_specific_citation(obligation, "ICDR", None)
        
        # Add AIBI reference if applicable
        obligation_lower = obligation.lower()
        for keyword, aibi_ref in self.aibi_mappings.items():
            if keyword in obligation_lower and "AIBI" not in base_citation:
                return f"{base_citation}; {aibi_ref}"
        
        return base_citation


def get_regulation_mapper():
    """Factory function"""
    return RegulationCitationMapper()


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """Test Regulation Mapper"""
    
    print("="*80)
    print("🧪 TESTING REGULATION CITATION MAPPER")
    print("="*80)
    
    mapper = RegulationCitationMapper()
    
    test_cases = [
        ("Details of Key Managerial Personnel must be disclosed", "ICDR"),
        ("Board meeting attendance records", "Companies Act"),
        ("Top 10 customers with percentage of sales", "ICDR"),
        ("Director qualifications and experience", "ICDR"),
        ("CSR expenditure details", "Companies Act"),
        ("Production and sales volume for last 3 years", "ICDR"),
    ]
    
    print("\nTest Cases:")
    print("-" * 80)
    
    for obligation, reg_type in test_cases:
        citation = mapper.get_specific_citation(obligation, reg_type)
        print(f"\nObligation: {obligation[:60]}...")
        print(f"Type: {reg_type}")
        print(f"Citation: {citation}")
    
    print("\n" + "="*80)
    print("✅ Regulation Mapper Tests Complete!")
    print("="*80)
