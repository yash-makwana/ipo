# engines/engine_3_content_review.py

import re
import os
import google.genai as genai
from google.genai import types
from data.checklists import NSE_ISSUES, ICDR_RULES, MANDATORY_BUSINESS_OVERVIEW
from engines.business_model_classifier import BusinessModelClassifier, RULES_ALLOWED
from engines.nse_micro_rules import MICRO_RULES
from engines.query_budget import QUERY_LIMITS

class GeminiReviewLayer:
    """
    V13 COGNITIVE LAYER: The Digital NSE Officer
    Uses Gemini to perform semantic reconciliation, intent analysis, and professional drafting.
    """
    def __init__(self):
        # Enable Gemini layer if either GOOGLE_API_KEY or GEMINI_API_KEY is present
        self.enabled = bool(os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"))
        if self.enabled:
            try:
                # Initialize genai client using provided key
                key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
                self.client = genai.Client(api_key=key)

                # Try candidate models and select the first working one
                models_to_try = [
                    "gemini-2.5-flash-lite",
                    "gemini-2.0-flash-lite",
                    "gemini-2.0-flash",
                    "gemini-2.5-flash",
                    "gemini-2.0-flash-exp",
                ]
                self.model_name = None
                for m in models_to_try:
                    try:
                        self.client.models.generate_content(
                            model=m,
                            contents="Test",
                            config=types.GenerateContentConfig(temperature=0.1, max_output_tokens=8)
                        )
                        self.model_name = m
                        break
                    except Exception:
                        continue

                if not self.model_name:
                    self.model_name = "gemini-2.0-flash-exp"

                print(f"✅ GeminiReviewLayer enabled (model: {self.model_name})")
            except Exception as e:
                print(f"⚠️  Gemini model initialization failed: {e}")
                self.enabled = False
        else:
            print("⚠️  GeminiReviewLayer disabled (no GOOGLE_API_KEY or GEMINI_API_KEY found)")
        
        self.system_prompt = """
        You are a Senior NSE Forensic Disclosure Auditor. You execute the "Perfect Parity" audit of DRHPs.

        CORE EVALUATION RULES (Non-Negotiable):
        1. RECONCILIATION: Explicitly reconcile Narrative vs Tables, Tables vs Tables, and Same Entity across Chapters.
        2. FORCED IMPACT: Every operational/financial gap MUST trigger a demand for [₹ impact and % of total revenue/cost/EBITDA/net worth].
        3. MASTER COMMENT AGGREGATION: Group repetitive micro-points (Trademarks, Jargon, Superlatives) into Authoritative Master Comments: "Throughout the Chapter (specifically on Page(s) X, Y, Z)..."
        4. OPERATIONAL HYGIENE AGENT: Explicitly audit for:
           - R&D Spend (₹ and % of revenue + 3FY trend).
           - QA Certifications vs Actual Inspection/Rejection rates.
           - Customer Churn and Repeat Business % (for revenue sustainability).
           - Logistics Mechanism (In-house vs Outsourced cost ratio).
           - CSR Execution (Budget vs Actual spend as per Cos Act).
           - Arm's Length RPT (Benchmark pricing for Related Party Transactions).
        5. SEVERITY RANKING: Use sub-rankings: [Critical - Valuation], [Critical - Legal], [Critical - Operational].
        6. FORWARD-LOOKING FLAG: Consolidate superlative/future claims into one master cautionary comment.
        7. TIME DIMENSION: All financial metrics MUST include 3 FYs + Dec 2024 stub period.
        8. COMPLIANCE CHECKLIST: Ensure all disclosures meet the NSE's "Perfect Parity" standard.
        9. INTENT LOCKING (CRITICAL):
            Before generating any query, identify the single examiner doubt triggered by the specific sentence or disclosure.
            - Do NOT broaden scope.
            - Do NOT generalize into strategy, projections, or unrelated metrics.
            - Generate queries ONLY to resolve that exact doubt, even if related data exists elsewhere in the DRHP.
            - If the issue is exclusion, ask rationale — not expansion.
            - If the issue is a claim, ask evidentiary basis — not performance.


        OUTPUT FORMAT (The Regulatory Letter):
        - Start with sub-severity tags. Use (a)/(b)/(c) structure.
        - Group related points across the entire chapter.
        - End with: "Confirm that the revised disclosure shall be updated in the Prospectus. Provide revised draft."
        """

    def audit_context(self, text_chunk, page_num, forensic_findings=None):
        if not self.enabled: return None
        
        prompt = f"""
        Context from DRHP Page {page_num}:
        ---
        {text_chunk}
        ---
        
        Forensic Findings (Exact Terms & Values):
        {forensic_findings if forensic_findings else "None identified."}
        
        TASK:
        Generate 1-3 professional NSE queries. 
        - Name the actual jargon/terms found (ONLY industrial/technical ones).
        - Quote the specific numeric values for any mismatches.
        - Do NOT number the queries.
        - Every query must end with "Provide revised draft...".
        - Do not use conversational language. Frame all questions as regulatory clarifications.
        - If multiple gaps exist, prioritize the one that would concern an NSE examiner the most.
.
        
        Output only the query text, each on a new line.
        """
        
        try:
            if not self.enabled or not getattr(self, 'client', None):
                return None

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[self.system_prompt, prompt],
                config=types.GenerateContentConfig(temperature=0.0, max_output_tokens=512)
            )

            # Response exposes .text similar to other usage in the codebase
            raw_queries = response.text.strip().split('\n')
            # Clean any accidental numbering from AI
            cleaned = []
            for q in raw_queries:
                c = re.sub(r"^[ivx\d+\.\-\s!]+", "", q.strip())
                if len(c) > 30: cleaned.append(c)
            return cleaned
        except Exception as e:
            print(f"[!] Gemini Error: {e}")
            return None


class IssueRegistry:
    def __init__(self):
        self._registry = {} # Key: Issue ID, Value: List of findings

    def register_finding(self, issue_id, page_num, snippet, full_match_text=None, full_match=None):
        if issue_id not in self._registry:
            self._registry[issue_id] = []
        for existing in self._registry[issue_id]:
            if existing['page'] == page_num and existing['full_match_text'] == full_match_text:
                return
        self._registry[issue_id].append({"page": page_num, "snippet": snippet, "full_match_text": full_match_text, "full_match": full_match})

    def get_findings(self, issue_id):
        return self._registry.get(issue_id, [])


class ContentReviewEngine:
    """
    ENGINE 3: NSE Content Review (CORE) - V13 COGNITIVE OVERHAUL
    """
    def __init__(self, doc_data, chapter_name="Business Overview"):
        self.doc_data = doc_data
        self.chapter_name = chapter_name
        self.registry = IssueRegistry()
        self.gemini = GeminiReviewLayer()
        self.queries = []
        
        # V27: STRUCTURAL ADVERSARIAL CONTROLS (NO PADDING)
        self.TARGET_QUOTA = 30
        self.MIN_QUOTA = 25
        self.MANDATORY_PILLARS = MANDATORY_BUSINESS_OVERVIEW
        self.ISSUE_REGISTRY = {} # {issue_code: {"first_page": int, "query_text": str}}
        
        # V26: SYSTEMIC CONTROLS
        self.classifier = BusinessModelClassifier()
        self.business_model = "HYBRID"
        self.query_counts = {}
        
        # State
        self.issue_inventory = [] # [{id, page, text, type}]
        
        # Forensic State
        self.acronyms_found = {}
        # V29: Forensic Repositories
        self.cross_check_registry = {
            "SKU_COUNT": {"values": {}, "patterns": [r"(\d+)\s+products?", r"(\d+)\s+SKUs?"]},
            "DISTRIBUTOR_COUNT": {"values": {}, "patterns": [r"(\d+)\s+distributors?"]},
            "LEASED_AREA": {"values": {}, "patterns": [r"(\d+(?:\.\d+)?)\s+(?:sq\.?\s*ft|sq\.?\s*mtrs)"]},
            "REVENUE_VALUE": {"values": {}, "patterns": [r"₹\s*(\d+(?:\.\d+)?)\s*(?:million|crore|lakhs?)"]},
            "REVENUE_TREND": {"values": {}, "patterns": [r"(?:Revenue|Sales|Income).*?(?:FY|Fiscal\s+Year|March)\s+(\d{4}).*?₹\s*(\d+(?:\.\d+)?)\s*(?:million|crore|lakhs?)"]}
        }
        self.superlatives_found = [] # [(page, snippet)]
        
        # Scope
        self.start_page = 1
        self.end_page = 372 

    def _classify_business(self, pages_text):
        """
        V26: Business Model Hard Switch.
        Detects if MANUFACTURING, SERVICES, or TRADING.
        """
        all_text = " ".join(list(pages_text.values())[:10]).lower() # Check first 10 pages
        
        m_keywords = ["manufacturing", "factory", "plant", "installed capacity", "production", "raw material", "machinery"]
        s_keywords = ["service", "software", "manpower", "platform", "consultancy", "solution provider"]
        t_keywords = ["trading", "retail", "wholesale", "distributor", "purchase of stock"]
        
        scores = {
            "MANUFACTURING": sum(1 for k in m_keywords if k in all_text),
            "SERVICES": sum(1 for k in s_keywords if k in all_text),
            "TRADING": sum(1 for k in t_keywords if k in all_text)
        }
        
        self.business_model = max(scores, key=scores.get)
        print(f"[*] V26: Business Model Classified as: {self.business_model}")
        return self.business_model

    def _calculate_evidence_score(self, text, issue):
        """
        V26: Evidence Scoring.
        numeric_value (+1), delta/YoY (+1), claim_language (+1).
        """
        score = 0
        snippet = text.lower()
        
        # 1. Numeric Presence
        if re.search(r"(\d+[\d,.]*\s?(%|lakhs|crores|mn|bn|₹))", snippet):
            score += 1
            
        # 2. Delta / YoY / Comparison
        delta_keywords = ["yoy", "increase", "decrease", "growth", "growth rate", "comparison", "delta", "change", "varianc"]
        if any(dk in snippet for dk in delta_keywords):
            score += 1
            
        # 3. Claim Language / Significance
        claim_keywords = ["significant", "major", "primarily", "key", "substantial", "material"]
        if any(ck in snippet for ck in claim_keywords):
            score += 1
            
        # Mandatory rules or definitions get a boost to pass
        if issue.get("mandatory") or issue["id"] == "UNDEFINED_JARGON":
            score += 2
            
        return score

    def _should_suppress_for_business(self, issue_id):
        """
        V27: Mandatory pillars bypass the business model gate.
        """
        if hasattr(self, 'MANDATORY_PILLARS') and issue_id in self.MANDATORY_PILLARS:
            return False

        allowed = RULES_ALLOWED.get(self.business_model)
        if allowed is None: return False
            
        return issue_id not in allowed

    def _apply_micro_rules(self, text, page_num):
        """
        V26: NSE Micro-Issue Detector.
        """
        for rule in MICRO_RULES:
            if re.search(rule["trigger_regex"], text, re.IGNORECASE):
                # Check global memory to avoid duplicates
                if rule["id"] not in self.ISSUE_REGISTRY:
                    self.ISSUE_REGISTRY[rule["id"]] = {
                        "first_page": page_num
                    }
                    self.issue_inventory.append({
                        "issue_id": rule["id"],
                        "page": page_num,
                        "text": f"{rule['query']}",
                        "type": "TYPE_MICRO"
                    })
                    print(f"[!] Micro-rule Triggered: {rule['id']} (Page {page_num})")

    def _get_global_forensic_summary(self):
        """
        Creates a compact summary of all forensic findings for Gemini to detect cross-page anomalies.
        """
        summary = []
        for issue_id, findings in self.registry._registry.items():
            for f in findings:
                summary.append(f"P.{f['page']}: {issue_id} found ('{f['full_match_text']}')")
        return "\n".join(summary[:50]) # Limit to top 50 for context efficiency

    def _explicitly_answered_with_numbers(self, text, issue):
        """
        V26: Procedural Adversary.
        A pillar is only cleared if it has HIGH-DENSITY quantitative proof.
        (e.g., at least 2 numbers in proximity).
        """
        regex = issue.get("primary_evidence_regex", r".*")
        matches = list(re.finditer(regex, text, re.IGNORECASE))
        
        if not matches: return False 
        
        clearance_count = 0
        for m in matches:
            # Tighter window: 100 chars
            proximity_window = text[max(0, m.start() - 100):min(len(text), m.end() + 100)]
            # REQUIRE: High density of numbers
            nums = re.findall(r"(\d+[\d,.]*\s?(%|lakhs|crores|mn|bn|₹))", proximity_window)
            if len(nums) >= 3: 
                clearance_count += 1
                
        return clearance_count >= 1

    def generate_queries(self, pages_text, forensic_enabled=True):
        print(f"[*] V28: Running Forensic Procedural Audit...")
        
        # 1. Classify Business Model
        self.business_model = self.classifier.classify(pages_text)
        
        # 2. STAGE 1: ISSUE INVENTORY (Mandatory Checklist)
        cleared_pillars = set()
        for pillar_id in self.MANDATORY_PILLARS:
            issue = next((i for i in NSE_ISSUES if i["id"] == pillar_id), None)
            if not issue or self._should_suppress_for_business(pillar_id):
                continue
                
            is_cleared = False
            first_found_page = None
            for page_num_str, text in pages_text.items():
                if self._explicitly_answered_with_numbers(text, issue):
                    is_cleared = True
                    cleared_pillars.add(pillar_id)
                    break
                if not first_found_page and re.search(issue["primary_evidence_regex"], text, re.IGNORECASE):
                    first_found_page = page_num_str

            if not is_cleared:
                # Use actual page if found, otherwise use first available page from pages_text
                if not first_found_page and pages_text:
                    first_found_page = list(pages_text.keys())[0]
                anchor_page = first_found_page if first_found_page else "(not found in chapter)"
                self.issue_inventory.append({
                    "issue_id": pillar_id,
                    "page": anchor_page,
                    "type": "TYPE_PROCEDURAL"
                })
                self.ISSUE_REGISTRY[pillar_id] = {"page": anchor_page}
        
        # --- V28: Forensic Extraction & Cross-Check ---
        self._forensic_extract_values(pages_text)
        self._detect_contradictions()

        # 3. STAGE 2: DISCOVERY (Deterministic, Micro, Superlatives & AI)
        for page_num_str, text in pages_text.items():
            self._apply_micro_rules(text, page_num_str)
            
            # Deterministic Issue Scrutiny
            for issue in NSE_ISSUES:
                if issue["id"] in self.MANDATORY_PILLARS: continue 
                if self._should_suppress_for_business(issue["id"]): continue
                
                m = re.search(issue["primary_evidence_regex"], text, re.IGNORECASE)
                if m:
                    if self._calculate_evidence_score(text, issue) >= 1:
                         self.registry.register_finding(issue["id"], page_num_str, m.group(0), m.group(0), m)

            # Superlative Tracking
            superlative_issue = next((i for i in NSE_ISSUES if i["id"] == "SUPERLATIVE_EVIDENCE"), None)
            if superlative_issue:
                matches = re.findall(superlative_issue["primary_evidence_regex"], text, re.IGNORECASE)
                self.superlatives_found.extend(matches)

            if self.gemini.enabled:
                ai_queries = self.gemini.audit_context(text, page_num_str)
                if ai_queries:
                    for q in ai_queries:
                        if len(q.strip()) > 50 and ("Page" in q or "page" in q):
                            self.issue_inventory.append({"text": q.strip(), "page": page_num_str, "type": "TYPE_AI"})

        # 4. STAGE 3: AGGREGATION & QUOTA
        self._aggregate_superlatives()
        self._finalize_deterministic_queries()

        current_count = len(self.issue_inventory) + len(self.queries)
        if current_count < self.MIN_QUOTA:
            deficit = self.TARGET_QUOTA - current_count
            forced_count = 0
            for pillar_id in self.MANDATORY_PILLARS:
                if deficit <= 0: break
                if any(it.get("issue_id") == pillar_id for it in self.issue_inventory): continue
                if pillar_id in cleared_pillars:
                    issue = next((i for i in NSE_ISSUES if i["id"] == pillar_id), None)
                    # Find actual page instead of using "General"
                    p_anchor = None
                    for p_num, p_text in pages_text.items():
                        if re.search(issue["primary_evidence_regex"], p_text, re.IGNORECASE):
                            p_anchor = p_num
                            break
                    # Fallback to first available page if not found
                    if not p_anchor and pages_text:
                        p_anchor = list(pages_text.keys())[0]
                    if p_anchor:
                        forced_count += 1
                        self.issue_inventory.append({
                            "issue_id": pillar_id, "page": p_anchor,
                            "type": "TYPE_PROCEDURAL", "forced_id": forced_count
                        })
                        deficit -= 1

        # 5. STAGE 4: WRITING
        self._write_queries()
        return self.queries

    def _forensic_extract_values(self, pages_text):
        for key, data in self.cross_check_registry.items():
            for p_num, text in pages_text.items():
                for pattern in data["patterns"]:
                    for match in re.finditer(pattern, text, re.IGNORECASE | re.DOTALL):
                        if key == "REVENUE_TREND":
                            year = match.group(1)
                            val = float(match.group(2).replace(",", ""))
                            if year not in data["values"]:
                                data["values"][year] = []
                            data["values"][year].append({"val": val, "page": p_num})
                        else:
                            val = float(match.group(1).replace(",", ""))
                            if p_num not in data["values"]:
                                data["values"][p_num] = []
                            data["values"][p_num].append({"val": val, "page": p_num})

    def _detect_contradictions(self):
        """Identifies discrepancies and trend declines across the document."""
        # 1. Standard Contradictions (SKU, Distributors, Area)
        for key in ["SKU_COUNT", "DISTRIBUTOR_COUNT", "LEASED_AREA"]:
            values_dict = self.cross_check_registry[key]["values"]
            if not values_dict: continue
            
            # Simple approach: compare first found values across pages
            pages = list(values_dict.keys())
            if len(pages) > 1:
                # Compare distinct pages
                base_page = pages[0]
                base_val = values_dict[base_page][0]["val"]
                
                for other_page in pages[1:]:
                    other_val = values_dict[other_page][0]["val"]
                    if abs(base_val - other_val) / (base_val or 1) > 0.02: # 2% threshold
                        item_name = key.replace('_', ' ').lower()
                        # Use actual page numbers, not "General"
                        page_ref = f"{base_page} and {other_page}"
                        self.queries.append({
                            "page": page_ref,
                            "text": f"If the narrative mentions the {item_name} as {base_val} on page {base_page} but the Table/another section reflects {other_val} on page {other_page}, kindly reconcile the factual contradiction and provide revised draft of the table along with confirmation that the same shall be updated in prospectus",
                            "type": "TYPE_CONTRADICTION",
                            "issue_id": "CROSS_PAGE_INCONSISTENCY",
                            "severity": "Major",
                            "category": "Forensic"
                        })

        # 2. Revenue Trend Decline Detection (Gold Standard Level 2)
        trend_data = self.cross_check_registry["REVENUE_TREND"]["values"]
        years = sorted(trend_data.keys())
        if len(years) >= 2:
            for i in range(len(years)-1):
                y_prev = years[i]
                y_curr = years[i+1]
                v_prev = max([d['val'] for d in trend_data[y_prev]])
                v_curr = max([d['val'] for d in trend_data[y_curr]])
                
                if v_curr < v_prev * 0.85: # >15% decline
                    self.queries.append({
                        "page": "General",
                        "text": f"It has been observed that the revenue declined substantially in {y_curr} (₹ {v_curr}) as compared to {y_prev} (₹ {v_prev}). Provide detailed reasons for the same. Provide revised draft along with confirmation.",
                        "type": "TYPE_CONTRADICTION",
                        "issue_id": "REVENUE_TREND_DECLINE",
                        "severity": "Major",
                        "category": "Financial"
                    })

    def _aggregate_superlatives(self):
        if not self.superlatives_found: return
        unique_superlatives = sorted(list(set(self.superlatives_found)))
        snippet = ", ".join([f"“{s}”" for s in unique_superlatives[:15]])
        issue = next((i for i in NSE_ISSUES if i["id"] == "SUPERLATIVE_EVIDENCE"), None)
        query_text = issue["consolidated_template"].format(snippet=snippet)
        self.issue_inventory.append({"text": query_text, "page": "Various", "type": "TYPE_MASTER"})

    def _write_queries(self):
        """
        V27: Finalizing the query objects.
        """
        for item in self.issue_inventory:
            if item["type"] == "TYPE_PROCEDURAL":
                issue = next((i for i in NSE_ISSUES if i["id"] == item["issue_id"]), None)
                if issue:
                    # Pass a fake 'findings' list to _create_observation that includes forced marker
                    fake_findings = [{"page": item["page"], "full_match_text": f"forced_metric_{item.get('forced_id', 0)}"}] if item.get("forced_id") else []
                    self._create_observation(issue, str(item["page"]), fake_findings, is_master=False)
            else:
                self.queries.append({
                    "page": item["page"],
                    "text": item.get("text", "[Material] Query text missing."),
                    "type": item["type"],
                    "issue_id": item.get("issue_id", "GENERAL"),
                    "severity": item.get("severity", "Material"),
                    "category": item.get("category", "General")
                })

    def _finalize_deterministic_queries(self):
        """
        V23: Aggregates repetitive micro-points into "Master Comments".
        Implements Sub-Severity Grading and Aggressive Range Merging.
        """
        print("[*] V23: Generating Master Comments & Sub-Severity Ranking...")
        
        quantitative_ids = {
            "SKU_RECONCILIATION", "DISTRIBUTOR_HEALTH_DETAIL", 
            "REVENUE_CHANNEL_BIFURCATION", "CAPACITY_CERTIFICATION", 
            "ATTRITION_RATE", "SUPPLIER_CONCENTRATION"
        }

        # Step 1: Map all findings by issue_id
        for issue_id in self.registry._registry:
            # V26: Global Memory/Budget Suppression
            if issue_id in self.ISSUE_REGISTRY:
                continue
            
            budget = QUERY_LIMITS.get(issue_id, 99)
            if self.query_counts.get(issue_id, 0) >= budget:
                continue

            issue = next((i for i in NSE_ISSUES if i["id"] == issue_id), None)
            if not issue: continue
            
            findings = self.registry.get_findings(issue_id)
            if not findings: continue
            
            # Sort findings by page
            findings.sort(key=lambda x: x['page'])
            
            # Master Comment Logic
            unique_pages = sorted(list(set(f['page'] for f in findings)))
            
            if len(unique_pages) >= 3 or len(findings) > 5:
                # Master Comment (Entire Chapter)
                # Anchor to first page
                page_str = f"{unique_pages[0]} to {unique_pages[-1]}"
                self._create_observation(issue, page_str, findings, is_master=True)
                
                # Registry Memory (Suppress further instance of this issue)
                self.ISSUE_REGISTRY[issue_id] = {"first_page": unique_pages[0]}
                self.query_counts[issue_id] = self.query_counts.get(issue_id, 0) + 1
            else:
                # Individual instances up to budget
                for page_num in unique_pages:
                    if self.query_counts.get(issue_id, 0) >= budget: break
                    
                    page_findings = [f for f in findings if f['page'] == page_num]
                    self._create_observation(issue, str(page_num), page_findings)
                    self.query_counts[issue_id] = self.query_counts.get(issue_id, 0) + 1

    def _create_observation(self, issue, page_str, findings, is_master=False):
        issue_id = issue["id"]
        category = issue.get("category", "Material")
        severity = issue.get("severity", "Material")  # ✅ ADDED - extract from issue definition
        
        # V29: LM DIRECTIVE TONE (Gold Standard Parity)
        # Use "LM is advised to" for Governance, Compliance, Legal, Risk, and Forensic issues
        lm_categories = ["Governance", "Compliance", "Legal", "Risk", "Forensic"]
        is_lm_directive = category in lm_categories or "RISK" in issue_id or "LM" in issue.get("consolidated_template", "")
        
        # Extract unique snippets
        unique_snippets = []
        seen_snippets = set()
        for fn in findings:
            s = fn.get('full_match_text', '').strip(" .,;:'\"")
            if not s or "forced_metric" in s: continue 
            if s.upper() not in seen_snippets:
                if issue_id == "UNDEFINED_JARGON":
                    if s.upper() in [e.upper() for e in issue.get("exclusions", [])]:
                        continue
                    if not s.isupper(): continue
                unique_snippets.append(s)
                seen_snippets.add(s.upper())
        
        # V27: Handle Forced pillars vs Normal findings
        is_forced = any("forced_metric" in fn.get('full_match_text', '') for fn in findings)
        
        if not unique_snippets:
            if findings and not is_forced:
                return # Findings were filtered out (e.g. jargons)
            else:
                # Use issue-specific descriptive placeholder (Fallback)
                item_name = issue['id'].replace('_', ' ').lower().replace('rpt', 'related party')
                snippet_str = f"the disclosure regarding {item_name}"
        else:
            # V29: Measurement unit formatting (semicolon separated with quotes)
            if issue_id == "MEASUREMENT_UNIT_CONSISTENCY":
                snippet_str = "; ".join([f"“{s}”" for s in unique_snippets[:8]])
            else:
                snippet_str = ", ".join([f"“{s}”" for s in unique_snippets[:5]])
            
        if is_master:
            snippet_str = f"various terms including {snippet_str}"

        # Severity Tagging
        prefix = ""
        
        # Use the REAL template from checklists.py
        base_template = issue.get('consolidated_template', "On page no. {anchor_pages}, disclosure regarding {snippet} requires clarification. Provide revised draft.")
        
        # V29: Assertive Tone Override (Refined for Final Polish)
        is_lm_directive = is_lm_directive and (base_template.startswith("LM") or issue.get('category') in ["Governance", "Compliance", "Legal"])
        
        if is_lm_directive:
             # Intelligent Rephrasing for high-stakes items
             query_text = base_template.format(anchor_pages=page_str, snippet=snippet_str)
             
             # IF already authoritative or hand-tuned, just use it
             if "LM is advised" in query_text or "LM shall confirm" in query_text:
                 final_query = query_text
             
             # IF starts with "Kindly", flip it if it's a critical category
             elif query_text.startswith("Kindly"):
                 final_query = f"LM is advised to {query_text[0].lower() + query_text[1:]}"
             
             else:
                 final_query = query_text # Fallback to template
        else:
            # V29: Standard "Kindly" tone (Matches user's latest examples)
            final_query = base_template.format(anchor_pages=page_str, snippet=snippet_str)
        
        print(f"[*] DEBUG: Generated query for {issue_id} (Page: {page_str})")
        
        self.queries.append({
            "page": page_str,
            "text": final_query,
            "type": "TYPE_PROCEDURAL" if not findings or is_forced else ("TYPE_MASTER" if is_master else "TYPE_DETERMINISTIC"),
            "issue_id": issue_id,  # ✅ ADDED for regulation mapping
            "severity": severity,  # ✅ ADDED for proper severity tracking
            "category": category   # ✅ ADDED for categorization
        })
