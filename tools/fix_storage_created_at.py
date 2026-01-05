"""Utility to repair job JSONs in storage by ensuring `created_at` is present.

Usage:
  python3 tools/fix_storage_created_at.py [--apply]

Without --apply the script will run in dry-run mode and print what it would change.
"""
import argparse
import json
from pathlib import Path
from datetime import datetime, UTC

STORAGE_DIR = Path(__file__).resolve().parents[1] / 'storage'


def repair_storage(apply_changes=False):
    changed = []
    skipped = []
    for p in STORAGE_DIR.glob('*.json'):
        try:
            data = json.loads(p.read_text())
        except Exception as e:
            skipped.append((p.name, f'malformed: {e}'))
            continue

        if data.get('created_at') in (None, ''):
            # Use file modification time as fallback
            mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=UTC).isoformat()
            if apply_changes:
                data['created_at'] = mtime
                p.write_text(json.dumps(data, indent=2, default=str))
            changed.append((p.name, mtime))

    return changed, skipped


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='Apply fixes to files')
    args = parser.parse_args()

    changed, skipped = repair_storage(args.apply)

    print(f'Found {len(changed)} files missing created_at')
    for name, value in changed:
        print(f'  {name}: set created_at -> {value}')
    if skipped:
        print(f'Skipped {len(skipped)} malformed files')
        for name, reason in skipped:
            print(f'  {name}: {reason}')


if __name__ == '__main__':
    main()
