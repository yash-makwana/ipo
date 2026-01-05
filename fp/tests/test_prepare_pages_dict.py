import os
import sys
import pytest

# Ensure project root is importable when running tests directly
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from multi_agent_orchestrator import MultiAgentComplianceOrchestrator


def test_prepare_pages_dict_accepts_page_number_and_page_key():
    orch = MultiAgentComplianceOrchestrator()

    # chunks using 'page_number'
    chunks = [
        {'chunk_id': 0, 'page_number': 1, 'text': 'Page one text part A.'},
        {'chunk_id': 1, 'page_number': 1, 'text': 'Page one text part B.'},
        {'chunk_id': 2, 'page_number': 2, 'text': 'Page two text.'}
    ]

    pages = orch._prepare_pages_dict(chunks)

    assert isinstance(pages, dict)
    assert 1 in pages and 2 in pages
    assert 'Page one text part A.' in pages[1]
    assert 'Page one text part B.' in pages[1]


def test_prepare_pages_dict_handles_legacy_page_key_and_empty_text():
    orch = MultiAgentComplianceOrchestrator()

    chunks = [
        {'chunk_id': 0, 'page': 3, 'text': 'Legacy page text.'},
        {'chunk_id': 1, 'page': 0, 'text': 'Orphan text without page'},
        {'chunk_id': 2, 'page_number': 4, 'text': ''}  # empty text should be handled
    ]

    pages = orch._prepare_pages_dict(chunks)

    # Legacy page should be present
    assert 3 in pages
    assert pages[3].startswith('Legacy page text')

    # Orphan chunk with page 0 should be skipped
    assert 0 not in pages

    # Page with empty text should still be present (key created with empty string)
    assert 4 in pages
    assert pages[4] == ''
