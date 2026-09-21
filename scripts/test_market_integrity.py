import json, os, tempfile, unittest
from unittest.mock import patch
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
from src.market import _eligible_rows, _validate_confirmatory_rows, confirmatory_writes_enabled, CONFIRMATORY_SECURITIES, BENCHMARK_TICKERS

class MarketIntegrityV2Tests(unittest.TestCase):
 def test_manual_or_push_run_is_dry_for_confirmatory_ledger(self):
  with patch.dict(os.environ,{"CONFIRMATORY_WRITE":"0"}): self.assertFalse(confirmatory_writes_enabled())
  with patch.dict(os.environ,{"CONFIRMATORY_WRITE":"1"}): self.assertTrue(confirmatory_writes_enabled())
 def test_confirmatory_batch_requires_all_15_series(self):
  rows=[]
  for t in list(CONFIRMATORY_SECURITIES)+list(BENCHMARK_TICKERS):
   rows.append({"ticker":t,"session_date":"2026-09-17","raw_close":100.0,"observed_at":"2026-09-18T22:00:00+00:00","source":"yahoo","collector":"yfinance","collector_version":"1.7.0","request":{},"series_type":"security" if t in CONFIRMATORY_SECURITIES else "benchmark","dividend":0.0,"split_ratio":0.0,"run_id":"123","commit_sha":"abc","frozen":True})
  self.assertTrue(_validate_confirmatory_rows(rows))
  with self.assertRaises(RuntimeError): _validate_confirmatory_rows(rows[:-1])
 def test_confirmatory_batch_rejects_nonfinite_actions(self):
  rows=[]
  for t in list(CONFIRMATORY_SECURITIES)+list(BENCHMARK_TICKERS):
   rows.append({"ticker":t,"session_date":"2026-09-17","raw_close":100.0,"observed_at":"2026-09-18T22:00:00+00:00","source":"yahoo","collector":"yfinance","collector_version":"1.7.0","request":{},"series_type":"security" if t in CONFIRMATORY_SECURITIES else "benchmark","dividend":0.0,"split_ratio":0.0,"frozen":True})
  rows[0]["dividend"]=float("nan")
  with self.assertRaises(ValueError): _validate_confirmatory_rows(rows)
 def test_last_vendor_bar_is_never_frozen(self):
  idx=pd.to_datetime(["2026-09-17","2026-09-18"])
  raw=pd.DataFrame({"Close":[100.0,101.0],"Adj Close":[99.0,100.0],"Dividends":[0.0,0.0],"Stock Splits":[0.0,0.0]},index=idx)
  rows=_eligible_rows(raw,["NVDA"],"2026-09-18T22:00:00+00:00","security")
  self.assertEqual([r["session_date"] for r in rows],["2026-09-17"])
 def test_duplicate_session_date_is_never_frozen(self):
  idx=pd.to_datetime(["2026-09-17","2026-09-18 00:00","2026-09-18 15:31"],format="mixed")
  raw=pd.DataFrame({"Close":[100,101,50],"Adj Close":[100,101,50],"Dividends":[0,0,0],"Stock Splits":[0,0,0]},index=idx)
  with self.assertRaises(ValueError):
   _eligible_rows(raw,["NVDA"],"2026-09-18T22:00:00+00:00","security")
 def test_vendor_split_adjustment_is_undone(self):
  idx=pd.to_datetime(["2026-01-13","2026-01-14","2026-01-15","2026-01-16"])
  raw=pd.DataFrame({"Close":[100,105,52.5,55],"Adj Close":[100,105,52.5,55],"Dividends":[0,0,0,0],"Stock Splits":[0,0,2,0]},index=idx)
  rows=_eligible_rows(raw,["NVDA"],"2026-01-17T00:00:00+00:00","security")
  self.assertEqual(rows[0]["raw_close"],200); self.assertEqual(rows[1]["raw_close"],210)
  self.assertEqual(rows[2]["raw_close"],52.5); self.assertEqual(rows[0]["vendor_split_factor"],2)
 def test_dividend_before_split_is_deadjusted(self):
  idx=pd.to_datetime(["2026-01-13","2026-01-14","2026-01-15","2026-01-16"])
  raw=pd.DataFrame({"Close":[50,50,25,25],"Adj Close":[49,49,25,25],"Dividends":[0,0.5,0,0],"Stock Splits":[0,0,2,0]},index=idx)
  rows=_eligible_rows(raw,["NVDA"],"2026-01-17T00:00:00+00:00","security")
  self.assertEqual(rows[1]["vendor_dividend"],0.5); self.assertEqual(rows[1]["dividend"],1.0)
  self.assertEqual(rows[1]["raw_close"],100.0)
 def test_raw_close_is_primary_and_actions_preserved(self):
  idx=pd.to_datetime(["2026-09-17","2026-09-18"])
  raw=pd.DataFrame({"Close":[100.0,101.0],"Adj Close":[98.0,99.0],"Dividends":[1.0,0.0],"Stock Splits":[2.0,0.0]},index=idx)
  r=_eligible_rows(raw,["NVDA"],"2026-09-18T22:00:00+00:00","security")[0]
  self.assertEqual(r["vendor_close"],100.0); self.assertEqual(r["vendor_adjusted_close"],98.0)
  self.assertEqual(r["dividend"],1.0); self.assertEqual(r["split_ratio"],2.0); self.assertTrue(r["frozen"])
if __name__=="__main__": unittest.main()
