import unittest
from datetime import datetime, date, timezone
from src.market import _last_complete_session_date

class MarketIntegrityTests(unittest.TestCase):
    def test_before_us_close_excludes_today(self):
        now=datetime(2026,9,18,18,0,tzinfo=timezone.utc)  # 14:00 ET
        self.assertEqual(_last_complete_session_date(now),date(2026,9,17))

    def test_after_us_close_allows_today(self):
        now=datetime(2026,9,18,21,0,tzinfo=timezone.utc)  # 17:00 ET
        self.assertEqual(_last_complete_session_date(now),date(2026,9,18))

if __name__=="__main__":
    unittest.main()
