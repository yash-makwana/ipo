# engines/engine_2_compliance.py

from data.checklists import ICDR_RULES

class StatutoryComplianceEngine:
    """
    ENGINE 2: Statutory Compliance
    
    Purpose:
    - Check compliance with ICDR Regulations / Companies Act.
    - This is a 'Background Signal'. It does not generate the main query list.
    - Used to flag HIGH SEVERITY issues that might need a Type D query in Engine 3.
    """
    
    def __init__(self, doc_data):
        self.doc_data = doc_data
        self.signals = [] # List of potential compliance flags

    def run_compliance_checks(self):
        print("[*] Engine 2: Running Statutory Compliance Checks (Background)...")
        full_text = "\n".join(self.doc_data['pages'].values())
        
        # Simple keyword-based compliance logic for demonstration
        # In a real system, this would be complex rules or RAG-based.
        
        # Check 1: Net Tangible Assets (Regulation 6)
        if "net tangible assets" not in full_text.lower():
            self.signals.append({
                "rule": ICDR_RULES["eligibility"],
                "status": "Check Required",
                "detail": "Could not find explicit mention of 'Net Tangible Assets'."
            })

        # Check 2: Promoter Contribution (Regulation 14)
        if "promoters' contribution" not in full_text.lower():
             self.signals.append({
                "rule": ICDR_RULES["promoter_contribution"],
                "status": "Check Required",
                "detail": "Promoters' contribution details missing."
            })
            
        print(f"[*] Engine 2: Generated {len(self.signals)} compliance backgrounds signals.")
        return self.signals
