import json
import os
import sys
import time
from typing import List, Dict, Any

# Ensure project root on sys.path when running as script
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from document_processor_local import process_pdf_with_docai, DocumentProcessor
from content_extraction_engine import get_content_extraction_engine
from expectation_locker import ExpectationLocker


def find_pdfs(upload_dir: str = './uploads') -> List[str]:
    pdfs = []
    for root, _, files in os.walk(upload_dir):
        for f in files:
            if f.lower().endswith('.pdf'):
                pdfs.append(os.path.join(root, f))
    return sorted(pdfs)


def evaluate_on_pdfs(pdfs: List[str], out_dir: str = './reports') -> Dict[str, Any]:
    os.makedirs(out_dir, exist_ok=True)
    locker = ExpectationLocker()
    engine = get_content_extraction_engine()

    summary = {
        'files_evaluated': 0,
        'expectation_stats': {},  # expectation_id -> {triggered, emitted}
        'files': {}
    }

    for pdf in pdfs:
        print(f"Evaluating: {pdf}")
        try:
            res = process_pdf_with_docai(pdf)
            pages = {p['page_number']: p['text'] for p in res['pages']}
            ctx = engine.extract_complete_context(pages)
            emitted = locker.detect_and_lock(ctx, pages)
            report = getattr(locker, 'last_detection_report', {}) or {}

            # Update stats structure to include missed reasons
            for e in locker.expectations:
                eid = e['id']
                if eid not in summary['expectation_stats']:
                    summary['expectation_stats'][eid] = {'triggered': 0, 'emitted': 0, 'missed': 0, 'miss_reasons': {}}

            # Use locker.report to count triggered/emitted/missed
            triggered_ids = report.get('triggered', [])
            for eid in triggered_ids:
                summary['expectation_stats'][eid]['triggered'] += 1

            for em in report.get('emitted', []):
                summary['expectation_stats'][em['expectation_id']]['emitted'] += 1

            for miss in report.get('missed', []):
                eid = miss['expectation_id']
                summary['expectation_stats'][eid]['missed'] += 1
                reason = miss.get('reason')
                if reason:
                    summary['expectation_stats'][eid]['miss_reasons'].setdefault(reason, 0)
                    summary['expectation_stats'][eid]['miss_reasons'][reason] += 1

            # Store file-level info
            summary['files'][os.path.basename(pdf)] = {
                'products_count': ctx['metadata']['products_count'],
                'segments_count': ctx['metadata']['segments_count'],
                'anomalies_count': ctx['metadata']['anomalies_count'],
                'emitted_questions': [e['expectation_id'] for e in report.get('emitted', [])],
                'missed_questions': [{ 'expectation_id': m['expectation_id'], 'reason': m.get('reason'), 'detail': m.get('detail') } for m in report.get('missed', [])]
            }

            summary['files_evaluated'] += 1
        except Exception as e:
            print(f"  Error evaluating {pdf}: {e}")
            continue

    # Compute derived metrics
    metrics = {}
    total_files = max(1, summary['files_evaluated'])
    covered_expectations = 0
    total_expectations = len(locker.expectations)
    mean_missed_rate = 0.0

    for eid, stats in summary['expectation_stats'].items():
        if stats['triggered'] > 0:
            covered_expectations += 1
            missed_rate = stats['emitted'] / stats['triggered'] if stats['triggered'] > 0 else 0.0
            mean_missed_rate += missed_rate

    coverage_rate = covered_expectations / total_expectations if total_expectations else 0.0
    mean_missed_rate = mean_missed_rate / covered_expectations if covered_expectations else 0.0

    metrics['expectation_coverage_rate'] = coverage_rate
    metrics['mean_missed_rate_for_triggered'] = mean_missed_rate
    metrics['files_evaluated'] = summary['files_evaluated']

    out = {'summary': summary, 'metrics': metrics, 'generated_at': time.time()}

    out_path = os.path.join(out_dir, f"expectation_eval_{int(time.time())}.json")
    with open(out_path, 'w') as f:
        json.dump(out, f, indent=2)

    print(f"Evaluation complete. Report saved to {out_path}")
    return out


if __name__ == '__main__':
    pdfs = find_pdfs('./uploads')
    if not pdfs:
        print('No PDFs found in uploads/. Place sample DRHPs under uploads/<id>/<file>.pdf')
    else:
        evaluate_on_pdfs(pdfs[:20])  # limit to first 20 by default
