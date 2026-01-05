from forensic_scanner import get_forensic_scanner
from regulation_mapper import get_regulation_mapper
from query_drafter import get_query_drafter
from data.checklists import NSE_ISSUES
from typing import List, Dict, Any
class ForensicOrchestrator:
    """
    Master coordinator for the 3-phase forensic architecture
    """
    
    def __init__(self):
        # Load checklist
        self.checklist = NSE_ISSUES
        
        # Initialize 3 phases
        self.scanner = get_forensic_scanner(self.checklist)
        self.mapper = get_regulation_mapper()
        self.drafter = get_query_drafter()
        
        print("✅ Forensic Orchestrator initialized (3-Phase)")
    
    def process_drhp(
        self, 
        pages_dict: Dict[int, str],
        chapter_name: str = "Business Overview"
    ) -> List[Dict]:
        """
        Complete 3-phase processing
        
        Args:
            pages_dict: {page_number: page_text}
            chapter_name: DRHP chapter being analyzed
        
        Returns:
            List of NSE-grade queries
        """
        
        print(f"\n{'='*80}")
        print(f"🔬 FORENSIC ANALYSIS - {chapter_name}")
        print(f"{'='*80}")
        print(f"   Pages to scan: {len(pages_dict)}")
        print(f"   Checklist items: {len(self.checklist)}")
        
        # ====================================================================
        # PHASE 1: THE ANCHOR (Deterministic Detection)
        # ====================================================================
        
        print(f"\n🎯 PHASE 1: Scanning with {len(self.checklist)} patterns...")
        findings = self.scanner.scan_document(pages_dict)
        print(f"   ✅ Found {len(findings)} potential issues")
        
        if not findings:
            print(f"   ℹ️ No issues detected - Document appears compliant")
            return []
        
        # ====================================================================
        # PHASE 2: THE ENRICHMENT (Knowledge Graph)
        # ====================================================================
        
        print(f"\n📚 PHASE 2: Enriching with regulation context...")
        enriched_findings = []
        
        for finding in findings:
            regulation = self.mapper.get_regulation_for_issue(
                finding['issue_id']
            )
            
            enriched_findings.append({
                'finding': finding,
                'regulation': regulation
            })
        
        print(f"   ✅ Enriched {len(enriched_findings)} findings")
        
        # ====================================================================
        # PHASE 3: THE VERDICT (LLM Drafting)
        # ====================================================================
        
        print(f"\n🧠 PHASE 3: Drafting NSE queries...")
        final_queries = []
        
        for item in enriched_findings:
            query = self.drafter.draft_query(
                finding=item['finding'],
                regulation=item['regulation']
            )
            
            final_queries.append(query)
        
        print(f"   ✅ Drafted {len(final_queries)} queries")
        
        # Sort by page number
        final_queries.sort(key=lambda x: x['page'])
        
        print(f"\n{'='*80}")
        print(f"✅ FORENSIC ANALYSIS COMPLETE")
        print(f"{'='*80}")
        
        return final_queries


def get_forensic_orchestrator():
    """Factory function"""
    return ForensicOrchestrator()