import json
import logging
import os
import re
from typing import Dict, List, Any


class ExpectationLocker:
    """Simple Expectation Locker prototype

    Responsibilities:
    - Load expectation ontology JSON
    - Detect triggered expectations using simple heuristics (string hints)
    - Check whether expectation seems satisfied based on DRHP context
    - Emit one precise question per unmet expectation (intent-locked)
    """

    def __init__(self, ontology_path: str = None):
        if ontology_path is None:
            ontology_path = os.path.join(os.path.dirname(__file__), 'config', 'expectation_ontology.json')

        with open(ontology_path, 'r') as f:
            self.ontology = json.load(f)

        # Precompute flat list of expectations
        self.expectations = []
        for ch in self.ontology.get('chapters', []):
            for exp in ch.get('expectations', []):
                exp_copy = exp.copy()
                exp_copy['chapter_id'] = ch['id']
                exp_copy['chapter_label'] = ch.get('label', ch['id'])
                self.expectations.append(exp_copy)
        # diagnostics from last run
        self.last_detection_report: Dict[str, Any] = {}
        # module logger
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            # basic default handler when used as script/CLI; library callers can configure logging
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(levelname)s:%(name)s:%(message)s'))
            self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def _text_join(self, pages_dict: Dict[int, str]) -> str:
        return "\n".join([t for _, t in sorted(pages_dict.items())]) if pages_dict else ""

    def _snippet_around(self, text: str, start: int, end: int, window: int = 120) -> str:
        s = max(0, start - window)
        e = min(len(text), end + window)
        return re.sub(r"\s+", " ", text[s:e]).strip()

    def _satisfies_evidence_reference(self, text: str, hints: List[str]) -> (bool, str, str):
        """Return (satisfied, detail, snippet) if a strong citation pattern exists near any hint occurrence.

        Strong citation patterns include explicit 'Source:' tokens, 'See page', parenthetical citations with years, or 'Market Research:'
        """
        citation_patterns = [r"\bSource[:\s-]", r"\bSee (page|table)\b", r"Market Research:", r"\(.*?\d{4}.*?\)", r"\(Source: [^)]+\)"]

        for h in hints:
            for m in re.finditer(re.escape(h), text, re.IGNORECASE):
                snippet = self._snippet_around(text, m.start(), m.end(), window=120)
                for pat in citation_patterns:
                    if re.search(pat, snippet, re.IGNORECASE):
                        return True, 'evidence_reference_strong', snippet

        return False, '', ''

    def _has_revenue_numbers_in_pages(self, pages: Dict[int, str], page_map: Dict[str, Any]) -> (bool, str, str):
        """Detect if revenue tables/sections include numeric cells nearby headers."""
        header_keywords = r"\b(product|segment|revenue|sales|amount)\b"
        number_pat = r"\d{1,3}(?:,\d{3})*(?:\.\d+)?"

        page_idxs = []
        if page_map and page_map.get('revenue_tables'):
            page_idxs = page_map.get('revenue_tables')
        else:
            # fallback: consider all pages
            page_idxs = list(pages.keys())

        for p in page_idxs:
            txt = pages.get(p, '')
            # look for header keywords and numbers within 200 chars
            for m in re.finditer(header_keywords, txt, re.IGNORECASE):
                snippet = self._snippet_around(txt, m.start(), m.end(), window=200)
                if re.search(number_pat, snippet):
                    return True, 'numeric_revenue_detected', snippet

        return False, '', ''

    def _satisfies_audited_financials(self, text: str) -> (bool, str, str):
        """Return True if audited financials inclusion appears strongly present (page refs or statement headers)."""
        # look for explicit phrase with page refs
        if re.search(r"audited financial statements", text, re.IGNORECASE):
            # check for page reference
            m = re.search(r"\b(page|pages)\s+\d{1,3}(?:\s*[-–]\s*\d{1,3})?\b", text, re.IGNORECASE)
            if m:
                return True, 'audited_with_page_refs', self._snippet_around(text, m.start(), m.end())

        # look for statement headers (Balance Sheet etc.)
        if re.search(r"\b(Balance Sheet|Statement of Profit and Loss|Profit and Loss Statement|Statement of Cash Flows|Auditor's Report)\b", text, re.IGNORECASE):
            return True, 'financial_statement_headers', self._snippet_around(text, 0, 0)

        return False, '', ''

    def _hint_present(self, hint: str, text: str) -> bool:
        # Simple substring match (case-insensitive) or regex when hint contains special tokens
        try:
            return re.search(re.escape(hint), text, re.IGNORECASE) is not None
        except Exception:
            return False

    def detect_and_lock(self, drhp_context: Dict[str, Any], pages_dict: Dict[int, str]) -> List[Dict[str, Any]]:
        """Detect expectations and return list of forced questions for unmet expectations

        Returns: list of {expectation_id, chapter_id, question, reason}
        Also populates `self.last_detection_report` with details of triggered, emitted and missed expectations and reasons.
        """
        text = self._text_join(pages_dict)
        emitted = []
        missed = []
        triggered_ids = []

        for exp in self.expectations:
            hints = exp.get('detection_hints', [])
            triggered = any(self._hint_present(h, text) for h in hints)

            if not triggered:
                continue

            triggered_ids.append(exp['id'])

            # Basic satisfaction checks based on expected_answer_type
            satisfied = False
            satisfied_by = None

            aet = exp.get('expected_answer_type', '')

            if aet == 'table':
                products = drhp_context.get('products', []) if drhp_context else []
                # Prefer numeric evidence: either product-level revenue numbers or revenue table with numbers
                # check product revenue_data values for numbers
                prod_has_numbers = False
                for p in products:
                    rd = p.get('revenue_data')
                    if isinstance(rd, dict) and any(re.search(r"\d", str(v)) for v in rd.values()):
                        prod_has_numbers = True
                        break
                if prod_has_numbers:
                    satisfied = True
                    satisfied_by = 'product_revenue_data'
                else:
                    ok, detail, snippet = self._has_revenue_numbers_in_pages(pages_dict, drhp_context.get('page_map', {}))
                    if ok:
                        satisfied = True
                        satisfied_by = detail

            elif aet == 'short_explanation':
                # require exclusion plus a rationale token nearby to be considered satisfied
                m = re.search(r'\b(exclude|excluded|exclusion|not included)\b', text, re.IGNORECASE)
                if m:
                    # look for rationale words in the same sentence
                    sent = re.split(r'[.\n]', text[max(0, m.start() - 200):m.end() + 200])
                    joined = ' '.join(sent)
                    if re.search(r'\b(because|due to|based on|as a result)\b', joined, re.IGNORECASE):
                        satisfied = True
                        satisfied_by = 'exclusion_with_rationale'

            elif aet == 'evidence_reference':
                ok, detail, snippet = self._satisfies_evidence_reference(text, exp.get('detection_hints', []))
                if ok:
                    satisfied = True
                    satisfied_by = detail
                    satisfied_snippet = snippet

            elif aet == 'numeric_summary':
                trends = drhp_context.get('trends', []) if drhp_context else []
                if trends:
                    satisfied = True
                    satisfied_by = 'numeric_trends_present'

            elif aet.startswith('document'):
                ok, detail, snippet = self._satisfies_audited_financials(text)
                if ok:
                    satisfied = True
                    satisfied_by = detail
                    satisfied_snippet = snippet

            # If satisfied, record missed reason
            if satisfied:
                entry = {
                    'expectation_id': exp['id'],
                    'chapter_id': exp['chapter_id'],
                    'reason': 'satisfied_by_heuristic',
                    'detail': satisfied_by
                }
                if 'satisfied_snippet' in locals() and satisfied_snippet:
                    entry['evidence_snippet'] = satisfied_snippet[:400]
                    del satisfied_snippet
                missed.append(entry)
                self.logger.debug(f"Expectation {exp['id']} triggered but marked satisfied: {satisfied_by}")
                continue

            # Not satisfied -> attempt to emit a single locked question
            q_template = exp.get('enforcement', {}).get('question_template', '')
            if not q_template or not q_template.strip():
                missed.append({
                    'expectation_id': exp['id'],
                    'chapter_id': exp['chapter_id'],
                    'reason': 'missing_question_template',
                    'detail': None
                })
                self.logger.warning(f"Expectation {exp['id']} has no question_template; skipping emission")
                continue

            # Fill simple placeholders if needed, recording fallback substitutions
            question = q_template
            placeholder_fallbacks = {}

            if '{{claim_text}}' in question:
                claim = self._extract_claim_snippet(text, exp.get('detection_hints', []))
                if not claim:
                    claim = 'the claim'
                    placeholder_fallbacks['claim_text'] = 'fallback_used'
                question = question.replace("{{claim_text}}", claim)

            if '{{risk_text}}' in question:
                risk = self._extract_claim_snippet(text, ['risk', 'risk factor'])
                if not risk:
                    risk = 'the risk'
                    placeholder_fallbacks['risk_text'] = 'fallback_used'
                question = question.replace('{{risk_text}}', risk)

            if '{{entity}}' in question:
                if drhp_context.get('products'):
                    question = question.replace('{{entity}}', drhp_context['products'][0].get('name', 'the entity'))
                else:
                    question = question.replace('{{entity}}', 'the entity')
                    placeholder_fallbacks['entity'] = 'fallback_used'

            emitted.append({
                'expectation_id': exp['id'],
                'chapter_id': exp['chapter_id'],
                'chapter_label': exp.get('chapter_label'),
                'question': question,
                'reason': 'triggered_and_emitted',
                'placeholders': placeholder_fallbacks
            })

        # Store detection report for downstream inspection
        self.last_detection_report = {
            'triggered': triggered_ids,
            'emitted': emitted,
            'missed': missed,
            'text_snippet': text[:400]
        }

        # Log summary at info level
        self.logger.info(f"ExpectationLocker run: triggered={len(triggered_ids)}, emitted={len(emitted)}, missed={len(missed)}")

        return emitted

    def _extract_claim_snippet(self, text: str, hints: List[str]) -> str:
        # Return a short phrase around the first hint occurrence
        for h in hints:
            m = re.search(re.escape(h), text, re.IGNORECASE)
            if m:
                start = max(0, m.start() - 30)
                end = min(len(text), m.end() + 60)
                return re.sub(r'\s+', ' ', text[start:end]).strip()
        return ''


def get_expectation_locker():
    return ExpectationLocker()
