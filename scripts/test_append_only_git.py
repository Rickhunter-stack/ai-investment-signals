import importlib.util
import unittest
from pathlib import Path

P = Path(__file__).parent / "check_append_only_git.py"
spec = importlib.util.spec_from_file_location("guard", P)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class AppendOnlyGuardTests(unittest.TestCase):
    def test_allows_append(self):
        old = [{"date": "2026-09-14", "score": 50}]
        new = old + [{"date": "2026-09-21", "score": 60}]
        guard.assert_list_prefix(old, new, "history.json")

    def test_rejects_historical_score_rewrite(self):
        old = [{"date": "2026-09-14", "score": 50}]
        rewritten = [{"date": "2026-09-14", "score": 99}]
        with self.assertRaisesRegex(ValueError, "historical entries"):
            guard.assert_list_prefix(old, rewritten, "history.json")

    def test_rejects_deletion(self):
        old = [{"id": "A"}, {"id": "B"}]
        with self.assertRaises(ValueError):
            guard.assert_list_prefix(old, old[:1], "events.json")


if __name__ == "__main__":
    unittest.main()
