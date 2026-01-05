import json
from pathlib import Path

from tools.fix_storage_created_at import repair_storage


def test_repair_storage_fills_missing_created_at(tmp_path):
    storage = Path(tmp_path)
    f1 = storage / 'a.json'
    f2 = storage / 'b.json'
    f1.write_text(json.dumps({'id': 'a', 'created_at': None}))
    f2.write_text(json.dumps({'id': 'b'}))

    # Temporarily point the module's STORAGE_DIR to tmp_path
    from importlib import reload
    import tools.fix_storage_created_at as fixer
    fixer.STORAGE_DIR = storage

    changed, skipped = repair_storage(apply_changes=True)
    assert len(changed) == 2

    # Verify files now have created_at
    for p in [f1, f2]:
        data = json.loads(p.read_text())
        assert data.get('created_at')
