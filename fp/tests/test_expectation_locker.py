import os
import sys

# Ensure local project root on path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from expectation_locker import ExpectationLocker


def test_emits_revenue_exclusion_question_when_missing():
    locker = ExpectationLocker()

    # Pages mention revenue table but products have no revenue_data
    pages = {1: 'Product wise revenue table present but no numbers', 2: 'Some narrative about sales'}
    drhp_context = {
        'products': [{'name': 'ProductA', 'revenue_data': {}}, {'name': 'ProductB', 'revenue_data': {}}],
        'page_map': {'business_overview': [1], 'revenue_tables': []},
        'trends': []
    }

    emitted = locker.detect_and_lock(drhp_context, pages)
    ids = [e['expectation_id'] for e in emitted]

    assert 'revenue_disclosure_completeness' in ids or 'revenue_disclosure_exclusions' in ids


def test_emits_superlative_question_with_claim_snippet():
    locker = ExpectationLocker()

    pages = {1: "We are the best in consumer electronics in the region, highest market share claimed."}
    drhp_context = {'products': [], 'page_map': {}, 'trends': []}

    emitted = locker.detect_and_lock(drhp_context, pages)
    # Should emit superlative_claims_source expectation question
    sup = [e for e in emitted if e['expectation_id'] == 'superlative_claims_source']
    assert len(sup) == 1
    assert 'evidentiary' in sup[0]['question'] or 'source' in sup[0]['question']


def test_normalizer_preserves_locked_queries():
    # Ensure BusinessModelNormalizer keeps queries marked locked
    from interpretation_normalization_layer import BusinessModelNormalizer

    normalizer = BusinessModelNormalizer()
    queries = [
        {'type': 'nse_expectation_question', 'issue_id': 'fake_expect', 'locked': True, 'observation': 'Please provide evidence.'},
        {'type': 'nse_content_query', 'issue_id': 'NOT_RELEVANT_ID', 'observation': 'Irrelevant query'}
    ]

    company_profile = {'business_type': 'Manufacturing', 'revenue': 0}
    out = normalizer.normalize(queries, company_profile)

    # Locked query should be preserved; irrelevant should be filtered
    assert any(q.get('locked') for q in out)
    assert not any(q.get('issue_id') == 'NOT_RELEVANT_ID' for q in out)


def test_reports_missed_reason_when_satisfied_by_evidence():
    locker = ExpectationLocker()

    # Pages have a superlative claim and a 'report' mention (satisfies evidence heuristic)
    # Note: with tightened heuristics a weak phrase like 'See our market report' is NOT considered strong evidence
    pages = {1: "We are the best in the region. See our market report published below."}
    drhp_context = {'products': [], 'page_map': {}, 'trends': []}

    emitted = locker.detect_and_lock(drhp_context, pages)
    report = locker.last_detection_report

    # With tightened heuristics this should emit the superlative question (weak evidence not accepted)
    ids = [e['expectation_id'] for e in emitted]
    assert 'superlative_claims_source' in ids


def test_superlative_strong_citation_satisfied_and_weak_citation_emitted():
    locker = ExpectationLocker()

    # Strong citation nearby -> considered satisfied
    pages = {1: "We are the best. Source: ABC Research 2022 (page 34)."}
    drhp_context = {'products': [], 'page_map': {}, 'trends': []}
    locker.detect_and_lock(drhp_context, pages)
    report = locker.last_detection_report
    missed = [m for m in report.get('missed', []) if m['expectation_id'] == 'superlative_claims_source']
    assert len(missed) == 1
    assert missed[0]['detail'] == 'evidence_reference_strong'

    # Weak citation phrase only -> should emit a question
    pages2 = {1: "We are the best. See our market report published below."}
    emitted = locker.detect_and_lock(drhp_context, pages2)
    ids = [e['expectation_id'] for e in emitted]
    assert 'superlative_claims_source' in ids


def test_revenue_completeness_detects_numbers_and_emits_when_missing():
    locker = ExpectationLocker()

    # No numeric revenue -> should emit completeness question
    pages = {1: 'Revenue table present but no numbers', 2: 'Narrative text only.'}
    drhp_context = {'products': [], 'page_map': {'revenue_tables': [1]}, 'trends': []}
    emitted = locker.detect_and_lock(drhp_context, pages)
    ids = [e['expectation_id'] for e in emitted]
    assert 'revenue_disclosure_completeness' in ids

    # Numeric revenue present -> considered satisfied
    # Use a phrase that matches the ontology hint for detection
    pages2 = {1: 'product wise revenue: ProductA — 1,234,567'}
    drhp_context2 = {'products': [], 'page_map': {'revenue_tables': [1]}, 'trends': []}
    locker.detect_and_lock(drhp_context2, pages2)
    report = locker.last_detection_report
    missed = [m for m in report.get('missed', []) if m['expectation_id'] == 'revenue_disclosure_completeness']
    assert len(missed) == 1
    assert missed[0]['detail'] == 'numeric_revenue_detected'


def test_audited_detection_requires_pages_or_headers():
    locker = ExpectationLocker()

    # Weak mention of 'audited financial statements' but no page refs should NOT be treated as satisfied
    pages = {1: 'Audited financial statements will be provided.'}
    drhp_context = {'products': [], 'page_map': {}, 'trends': []}
    emitted = locker.detect_and_lock(drhp_context, pages)
    ids = [e['expectation_id'] for e in emitted]
    assert 'audited_financials_provided' in ids

    # Strong audited mention with pages should be satisfied
    pages2 = {1: 'Audited financial statements are included (pages 45-48).'}
    locker.detect_and_lock(drhp_context, pages2)
    report = locker.last_detection_report
    missed = [m for m in report.get('missed', []) if m['expectation_id'] == 'audited_financials_provided']
    assert len(missed) == 1
    assert missed[0]['detail'] == 'audited_with_page_refs'
