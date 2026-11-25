"""Decide whether scheduled catalog work is due; manual/push runs stay unconditional."""
import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

REQUIRED_SHOPS = ('acer', 'coolblue', 'smartphonehoesjes')


def refresh_due(root, event, now):
    if event != 'schedule':
        return True, 'Manual or source-change run'
    paths = set((root / 'data').glob('*/manifest.json'))
    paths.update(root / 'data' / shop / 'manifest.json' for shop in REQUIRED_SHOPS)
    for path in sorted(paths):
        try:
            stamp = json.loads(path.read_text())['fetchedAt']
            fetched = datetime.fromisoformat(stamp.replace('Z', '+00:00'))
            if fetched.tzinfo is None:
                raise ValueError('Timestamp must have a timezone')
            age = now - fetched
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            return True, f'{path.parent.name}: missing or invalid timestamp'
        if age >= timedelta(hours=6) or age < -timedelta(minutes=5):
            return True, f'{path.parent.name}: refresh needed'
    return False, 'All catalog timestamps are less than six hours old'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--github-output', type=Path)
    args = parser.parse_args()
    due, reason = refresh_due(Path(__file__).resolve().parents[1],
                              os.environ.get('GITHUB_EVENT_NAME', ''),
                              datetime.now(timezone.utc))
    value = str(due).lower()
    print(f'Refresh due: {value}. {reason}')
    if args.github_output:
        with args.github_output.open('a') as output:
            output.write(f'due={value}\n')


if __name__ == '__main__':
    main()
