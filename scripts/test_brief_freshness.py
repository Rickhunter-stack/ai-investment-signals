import json, tempfile, unittest
from datetime import datetime, timezone
from pathlib import Path
from check_brief_freshness import check

def write(root, name, captured):
    events = [{"event_id": f"EVT-{name}", "captured_at": c} for c in captured]
    (root / f"{name}.json").write_text(json.dumps(events), encoding="utf-8")

class BriefFreshnessTest(unittest.TestCase):
    def test_recent_capture_is_fresh(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); write(root, "2026-10-03", ["2026-10-03T08:10:00+02:00"]); write(root, "2026-10-04", ["2026-10-04T08:10:00+02:00"])
            ok, message = check(datetime(2026, 10, 4, 12, 0, tzinfo=timezone.utc), 24, root)
            self.assertTrue(ok); self.assertIn("EVT-2026-10-04", message)

    def test_missing_day_is_stale(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); write(root, "2026-10-03", ["2026-10-03T08:10:00+02:00"])
            ok, _ = check(datetime(2026, 10, 4, 12, 0, tzinfo=timezone.utc), 24, root)
            self.assertFalse(ok)

    def test_empty_history_is_stale(self):
        with tempfile.TemporaryDirectory() as d:
            ok, message = check(datetime(2026, 10, 4, tzinfo=timezone.utc), 24, Path(d))
            self.assertFalse(ok); self.assertIn("no brief event", message)

if __name__ == "__main__": unittest.main()
