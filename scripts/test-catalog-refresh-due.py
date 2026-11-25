import json
import runpy
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

module = runpy.run_path(str(Path(__file__).with_name('catalog-refresh-due.py')))
refresh_due = module['refresh_due']


class RefreshDueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.now = datetime(2026, 11, 25, 19, tzinfo=timezone.utc)
        for shop in module['REQUIRED_SHOPS']:
            self.write(shop, self.now - timedelta(hours=5, minutes=59))

    def write(self, shop, stamp):
        path = self.root / 'data' / shop / 'manifest.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({'fetchedAt': stamp.isoformat()}))

    def due(self, event='schedule'):
        return refresh_due(self.root, event, self.now)[0]

    def test_fresh_schedule_skips_but_manual_and_push_refresh(self):
        self.assertFalse(self.due())
        self.assertTrue(self.due('workflow_dispatch'))
        self.assertTrue(self.due('push'))

    def test_six_hour_boundary_and_stale_other_shop_refresh(self):
        self.write('expert', self.now - timedelta(hours=6))
        self.assertTrue(self.due())

    def test_missing_required_manifest_repairs_instead_of_skipping(self):
        (self.root / 'data' / 'acer' / 'manifest.json').unlink()
        self.assertTrue(self.due())

    def test_invalid_and_future_timestamps_do_not_skip_repairs(self):
        path = self.root / 'data' / 'acer' / 'manifest.json'
        for content in ('{', '{}', '{"fetchedAt": null}',
                        '{"fetchedAt": "2026-11-25T18:00:00"}'):
            path.write_text(content)
            self.assertTrue(self.due())
        self.write('acer', self.now + timedelta(hours=1))
        self.assertTrue(self.due())

    def test_offset_timestamp_compared_in_utc(self):
        self.write('acer', datetime(2026, 11, 25, 15, tzinfo=timezone(timedelta(hours=2))))
        self.assertTrue(self.due())


if __name__ == '__main__':
    unittest.main()
