import json, os, tempfile, unittest
from unittest.mock import patch
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
from src.market import _eligible_rows, confirmatory_writes_enabled

class MarketIntegrityV2Tests(unittest.TestCase):
 def test_manual_or_push_run_is_dry_for_confirmatory_ledger(self):
  with patch.dict(os.environ,{"CONFIRMATORY_WRITE":"0"}): self.assertFalse(confirmatory_writes_enabled())
  with patch.dict(os.environ,{"CONFIRMATORY_WRITE":"1"}): self.assertTrue(confirmatory_writes_enabled())
 def test_last_vendor_bar_is_never_frozen(self):
  idx=pd.to_datetime(["2026-09-17","2026-09-18"])
  raw=pd.DataFrame({"Close":[100.0,101.0],"Adj Close":[99.0,100.0],"Dividends":[0.0,0.0],"Stock Splits":[0.0,0.0]},index=idx)
  rows=_eligible_rows(raw,["NVDA"],"2026-09-18T22:00:00+00:00","security")
  self.assertEqual([r["session_date"] for r in rows],["2026-09-17"])
 def test_raw_close_is_primary_and_actions_preserved(self):
  idx=pd.to_datetime(["2026-09-17","2026-09-18"])
  raw=pd.DataFrame({"Close":[100.0,101.0],"Adj Close":[98.0,99.0],"Dividends":[1.0,0.0],"Stock Splits":[2.0,0.0]},index=idx)
  r=_eligible_rows(raw,["NVDA"],"2026-09-18T22:00:00+00:00","security")[0]
  self.assertEqual(r["raw_close"],100.0); self.assertEqual(r["vendor_adjusted_close"],98.0)
  self.assertEqual(r["dividend"],1.0); self.assertEqual(r["split_ratio"],2.0); self.assertTrue(r["frozen"])
if __name__=="__main__": unittest.main()
