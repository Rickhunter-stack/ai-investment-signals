import sqlite3
import unittest

from src.db import SCHEMA


class MarketPointInTimeTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        self.conn.executescript(SCHEMA)

    def tearDown(self):
        self.conn.close()

    def test_provider_revision_cannot_overwrite_frozen_price(self):
        row = ('NVDA','2026-09-17',180.0,1000,'2026-09-17T21:20:00+00:00','yfinance','security')
        revised = ('NVDA','2026-09-17',999.0,1000,'2026-09-18T21:20:00+00:00','yfinance','security')
        sql = '''INSERT OR IGNORE INTO market_pit
                 (ticker,date,adjusted_close,volume,observed_at,source,series_type)
                 VALUES(?,?,?,?,?,?,?)'''
        self.conn.execute(sql, row); self.conn.execute(sql, revised)
        value = self.conn.execute("SELECT adjusted_close FROM market_pit WHERE ticker='NVDA' AND date='2026-09-17'").fetchone()[0]
        self.assertEqual(value, 180.0)

    def test_security_and_benchmark_share_same_price_field(self):
        sql = '''INSERT INTO market_pit
                 (ticker,date,adjusted_close,volume,observed_at,source,series_type)
                 VALUES(?,?,?,?,?,?,?)'''
        self.conn.execute(sql, ('NVDA','2026-09-17',180,None,'2026-09-17T21:20:00+00:00','yfinance','security'))
        self.conn.execute(sql, ('QQQ','2026-09-17',600,None,'2026-09-17T21:20:00+00:00','yfinance','benchmark'))
        rows = self.conn.execute('SELECT ticker, adjusted_close, series_type FROM market_pit ORDER BY ticker').fetchall()
        self.assertEqual({r[2] for r in rows}, {'security','benchmark'})
        self.assertTrue(all(r[1] > 0 for r in rows))


if __name__ == '__main__':
    unittest.main()
