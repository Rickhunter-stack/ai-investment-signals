import unittest
from validate_brief_events import validate_append_only
from test_brief_events import sample_event

class HistoryGuardTests(unittest.TestCase):
    def test_append_is_allowed(self):
        first=sample_event(); second=sample_event(); second["event_id"]="EVT-20260917-EFGH"; second["captured_at"]="2026-09-17T09:00:00+02:00"
        validate_append_only([first],[first,second])
    def test_historical_edit_is_rejected(self):
        first=sample_event(); edited=dict(first); edited["title"]="Edited after the fact"
        with self.assertRaises(ValueError): validate_append_only([first],[edited])

if __name__=="__main__": unittest.main()
