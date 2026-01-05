import json
from pathlib import Path

import main_local


def test_get_user_history_handles_none_created_at(tmp_path):
    # Point STORAGE_DIR to tmp_path for isolation
    main_local.STORAGE_DIR = Path(tmp_path)

    job1 = {'id': '1', 'user_email': 'u@example.com', 'created_at': '2026-01-02T00:00:00Z'}
    job2 = {'id': '2', 'user_email': 'u@example.com', 'created_at': None}
    job3 = {'id': '3', 'user_email': 'other@example.com', 'created_at': '2026-01-03T00:00:00Z'}

    (tmp_path / 'job1.json').write_text(json.dumps(job1))
    (tmp_path / 'job2.json').write_text(json.dumps(job2))
    (tmp_path / 'job3.json').write_text(json.dumps(job3))

    reports = main_local.get_user_history(user_email='u@example.com', limit=10)

    assert len(reports) == 2
    # job1 (with a timestamp) should come before job2 (None)
    assert [r['id'] for r in reports] == ['1', '2']
    # Ensure internal helper key is not leaked
    assert all('_created_at_str' not in r for r in reports)


def test_save_job_adds_created_at(tmp_path):
    main_local.STORAGE_DIR = Path(tmp_path)

    job_id = 'abc'
    job = {'id': job_id, 'user_email': 'u@example.com'}
    main_local.save_job(job_id, job)

    saved = json.loads((Path(tmp_path) / f"{job_id}.json").read_text())
    assert 'created_at' in saved and saved['created_at']


def test_get_user_history_skips_malformed_files(tmp_path):
    main_local.STORAGE_DIR = Path(tmp_path)

    good = {'id': 'good', 'user_email': 'u@example.com', 'created_at': '2026-01-04T00:00:00Z'}
    (tmp_path / 'good.json').write_text(json.dumps(good))
    # malformed json
    (tmp_path / 'bad.json').write_text('{ this is not: json }')

    reports = main_local.get_user_history(user_email='u@example.com', limit=10)
    assert len(reports) == 1
    assert reports[0]['id'] == 'good'
