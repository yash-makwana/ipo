import os
import sys

# Ensure project root is importable
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.expectation_evaluator import evaluate_on_pdfs


def test_evaluator_on_synthetic_pdf(tmp_path, monkeypatch):
    # Create a synthetic PDF-like folder with a small file (we'll reuse content_extraction engine directly)
    # But to keep test light, we'll mock find_pdfs and process_pdf_with_docai
    from tools import expectation_evaluator as ee

    # Monkeypatch find_pdfs to return empty list -> evaluator should return with 0 files
    monkeypatch.setattr(ee, 'find_pdfs', lambda *args, **kwargs: [])

    out = ee.evaluate_on_pdfs([])
    assert out['metrics']['files_evaluated'] == 0
