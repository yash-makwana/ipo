# PR: Tighten ExpectationLocker heuristics, add instrumentation and tests

## Summary
This PR tightens several heuristics in the Expectation Locker to reduce false-positives for expectation satisfaction, adds structured diagnostics to explain missed expectations, expands tests, and updates the evaluation harness to surface miss reasons.

## Changes
- `expectation_locker.py` (major)
  - Added helper functions:
    - `_satisfies_evidence_reference(...)` — enforces stronger citation patterns (e.g., `Source:`, `See page`, parenthetical citations with year).
    - `_has_revenue_numbers_in_pages(...)` — detects numeric cells near revenue headers in page content.
    - `_satisfies_audited_financials(...)` — requires page references or recognized statement headers.
  - Replaced permissive heuristics with stricter checks for expectations:
    - `superlative_claims_source` now requires strong citation patterns to be considered satisfied.
    - `revenue_disclosure_completeness` now requires numeric revenue evidence (product-level or table numbers).
    - `audited_financials_provided` now requires page refs or financial statement headers.
  - Adds `self.last_detection_report` containing `triggered / emitted / missed` lists and evidence snippets for diagnostics.

- `tools/expectation_evaluator.py` (minor)
  - Uses `last_detection_report` to populate `miss_reasons` and `missed_questions` in the report JSON.

- `config/expectation_ontology.json` (minor)
  - Added `"audited financial statements"` to detection hints.

- `tests/test_expectation_locker.py` (tests)
  - New tests for strong vs weak evidence, numeric revenue detection, audited page refs, and missed reason reporting.

## Tests
- Unit tests: `pytest tests/test_expectation_locker.py` — all tests pass.

## Evaluations
- Run the evaluator to check change impact:
  - `./venv/bin/python3 tools/expectation_evaluator.py` (limits to first 20 PDFs by default)
  - Inspect `./reports/expectation_eval_<timestamp>.json` for per-expectation `miss_reasons`.

## Motivation & Rationale
- Previous heuristics were too permissive (e.g., counting a generic mention of “report” as sufficient evidence), which suppressed useful, precise verification questions. Tightening the heuristics increases the likelihood of emitting a single, intent-locked question where a real evidentiary gap exists.

## Follow-ups / To Do
- Implement strict `revenue_disclosure_timeliness` detection (require FY labels / 3-year table column headers) — high priority.
- Consider adding small NLU heuristics or a lightweight classifier for borderline evidence detection if heuristics alone are insufficient.

## How to review
- Review `expectation_locker.py` changes and new helper functions.
- Run unit tests and the evaluator, compare the generated JSON report(s) to verify reduced false-satisfaction and improved question emission.

---
*If you'd like, I can open the branch and create the PR* (I can also prepare a short changelog entry for the repo release notes).