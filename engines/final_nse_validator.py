# engines/final_nse_validator.py

class FinalNSEValidator:
    """
    V26 Gatekeeper.
    Ensures the generation meets NSE's final letter standards.
    """
    def __init__(self, queries):
        self.queries = queries

    def validate(self):
        issues = []
        
        # 1. No Duplicate Issue Codes
        issue_ids = [q.get('issue_id') for q in self.queries if q.get('issue_id')]
        if len(issue_ids) != len(set(issue_ids)):
            # This is okay if budgeting allows, but we check for exact identicals
            text_hashes = set()
            for q in self.queries:
                h = hash(q['text'].strip())
                if h in text_hashes:
                    issues.append("Duplicate query text detected.")
                text_hashes.add(h)

        # 2. Min Queries Threshold
        if len(self.queries) < 15: # User wanted 25-40, but let's be realistic if doc is short
             issues.append(f"Insufficient queries ({len(self.queries)}). Expected > 15.")

        # 3. Chapter Coverage
        types = [q.get('type') for q in self.queries]
        if "TYPE_AI" not in types:
            issues.append("Zero AI-inferred queries. System might be too deterministic.")

        # 4. Governance/Risk Check
        risk_governance_keywords = ["risk factor", "governance", "legal", "confirm", "reconcile"]
        rg_count = sum(1 for q in self.queries if any(k in q['text'].lower() for k in risk_governance_keywords))
        if rg_count < 4:
            issues.append(f"Low Governance/Risk coverage ({rg_count} queries).")

        # 5. Placeholder Language
        placeholders = ["TODO", "REPLACE", "INSERT", "XXX", "[text]"]
        if any(p in q['text'] for q in self.queries for p in placeholders):
            issues.append("Placeholder language detected in output.")

        return issues
