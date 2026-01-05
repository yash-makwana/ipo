import re
from typing import List, Dict, Any

class ForensicScanner:
    """
    Phase 1: The Anchor
    Deterministic detection using regex patterns from checklists
    """
    
    def __init__(self, checklist: List[Dict]):
        self.checklist = checklist
        print(f"✅ Forensic Scanner loaded with {len(checklist)} checks")
    
    def scan_page(self, page_text: str, page_number: int) -> List[Dict]:
        """
        Scan a single page for all checklist patterns
        
        Returns:
            List of findings with context
        """
        findings = []
        
        for check in self.checklist:
            issue_id = check['id']
            pattern = check.get('primary_evidence_regex')
            
            if not pattern:
                continue
            
            # Find all matches
            matches = list(re.finditer(pattern, page_text, re.IGNORECASE))
            
            if matches:
                # For each match, extract context
                for match in matches:
                    snippet = self._extract_context(
                        page_text, 
                        match.start(), 
                        match.end()
                    )
                    
                    findings.append({
                        'issue_id': issue_id,
                        'page': page_number,
                        'matched_text': match.group(0),
                        'snippet': snippet,
                        'severity': check.get('severity', 'Material'),
                        'category': check.get('category', 'Operational'),
                        'template': check.get('consolidated_template'),
                        'intent': check.get('intent', '')
                    })
        
        return findings
    
    def _extract_context(self, text: str, start: int, end: int, 
                        context_chars: int = 300) -> str:
        """Extract text around match for context"""
        ctx_start = max(0, start - context_chars)
        ctx_end = min(len(text), end + context_chars)
        
        snippet = text[ctx_start:ctx_end]
        
        # Clean up
        snippet = ' '.join(snippet.split())  # Normalize whitespace
        
        return snippet
    
    def scan_document(self, pages_dict: Dict[int, str]) -> List[Dict]:
        """
        Scan entire document
        
        Args:
            pages_dict: {page_number: page_text}
        
        Returns:
            All findings across document
        """
        all_findings = []
        
        for page_num, page_text in pages_dict.items():
            page_findings = self.scan_page(page_text, page_num)
            all_findings.extend(page_findings)
        
        return all_findings


def get_forensic_scanner(checklist):
    """Factory function"""
    return ForensicScanner(checklist)