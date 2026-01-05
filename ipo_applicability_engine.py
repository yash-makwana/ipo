"""
IPO Applicability Engine - ENHANCED
===================================
"""
import re
from typing import Dict, List, Tuple

class IPOApplicabilityEngine:
    def __init__(self):
        print("✅ IPO Applicability Engine initialized")
    
    def infer(self, full_text: str) -> Dict[str, bool]:
        """Infer IPO characteristics from DRHP text"""
        text = full_text.lower()
        
        return {
            # Debt instruments
            "has_convertible_debt": bool(
                re.search(r'convertible\s+debt|debenture|ncd|convertible\s+bond', text)
            ),
            
            # Warrants
            "has_warrants": bool(
                re.search(r'\bwarrant(s)?\b', text)
            ),
            
            # Secured instruments
            "has_secured_instruments": bool(
                re.search(r'charge\s+on\s+assets|secured\s+by|mortgage|hypothecation|pledge', text)
            ),
            
            # Superior voting
            "has_sr_shares": bool(
                re.search(r'superior\s+voting|sr\s+equity|differential\s+voting', text)
            ),
            
            # VC/PE investors
            "has_vc_or_pe": bool(
                re.search(r'venture\s+capital|private\s+equity|aif\s+category|fvc(i)?', text)
            ),
            
            # Employee equity
            "has_employee_equity": bool(
                re.search(r'esop|employee\s+stock|sweat\s+equity|employee.*option', text)
            ),
            
            # Promoter contribution
            "mentions_promoter_contribution": bool(
                re.search(r'promoter(s)?\s+contribution', text)
            ),
            
            # Lock-in
            "mentions_lockin": bool(
                re.search(r'lock[- ]?in', text)
            ),
            
            # NEW: Rights issue
            "has_rights_issue": bool(
                re.search(r'rights\s+issue|rights\s+entitlement', text)
            ),
            
            # NEW: QIP
            "has_qip": bool(
                re.search(r'qualified\s+institutional\s+placement|qip', text)
            ),
        }
    
    def is_query_applicable(self, query_category: str, ipo_profile: Dict[str, bool]) -> bool:
        """Decide if query should be shown"""
        category = query_category.lower()
        
        # Suppress debt-related
        if any(word in category for word in ["debenture", "convertible debt", "ncd"]):
            return ipo_profile.get("has_convertible_debt", True)
        
        # Suppress warrant
        if "warrant" in category:
            return ipo_profile.get("has_warrants", True)
        
        # Suppress secured asset
        if any(word in category for word in ["security", "charge", "mortgage"]):
            return ipo_profile.get("has_secured_instruments", True)
        
        # Suppress SR shares
        if any(word in category for word in ["sr equity", "superior voting"]):
            return ipo_profile.get("has_sr_shares", True)
        
        # Suppress VC/PE
        if any(word in category for word in ["venture capital", "aif", "fvci"]):
            return ipo_profile.get("has_vc_or_pe", True)
        
        # Suppress ESOP
        if "esop" in category or "employee stock" in category:
            return ipo_profile.get("has_employee_equity", True)
        
        # Default: keep query
        return True