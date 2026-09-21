import importlib.util, unittest
from datetime import date, datetime, timezone
from pathlib import Path
P=Path(__file__).parent/"compute_outcomes.py"; s=importlib.util.spec_from_file_location("o",P); o=importlib.util.module_from_spec(s); s.loader.exec_module(o)

def row(t,d,p,obs="2026-09-22T21:00:00+00:00",div=0,split=0):
 return {"ticker":t,"session_date":d,"raw_close":p,"observed_at":obs,"dividend":div,"split_ratio":split,"frozen":True}

class OutcomeTests(unittest.TestCase):
 def test_calendar_month(self): self.assertEqual(o.add_months(date(2026,1,31),1),date(2026,2,28))
 def test_first_common_trading_day(self):
  m={"NVDA":[row("NVDA","2026-09-21",100),row("NVDA","2026-09-22",101)],"QQQ":[row("QQQ","2026-09-22",500)]}
  self.assertEqual(o.common_row(m,"NVDA","QQQ",date(2026,9,21))[0],date(2026,9,22))
 def test_total_return_reinvests_dividend(self):
  m=[row("X","2026-01-01",100),row("X","2026-02-01",100,div=10)]
  self.assertAlmostEqual(o.total_return(m,date(2026,1,1),date(2026,2,1)),.1)
 def test_append_never_rewrites(self):
  old=[{"outcome_id":"A","excess_return":.1}]; new=[{"outcome_id":"A","excess_return":9.9},{"outcome_id":"B"}]
  got=o.append_unique(old,new); self.assertEqual(got[0]["excess_return"],.1); self.assertEqual(len(got),2)
 def test_pre_protocol_snapshot_excluded(self):
  snaps=[{"date":"2026-09-14","captured_at":"2026-09-14T21:00:00+00:00","frozen":True,"method_version":"weekly-v1.0","scores":{"NVDA":{"signal_score":80}}}]
  self.assertEqual(o.build_rows(snaps,{},datetime(2027,1,1,tzinfo=timezone.utc)),[])
if __name__=="__main__": unittest.main()
