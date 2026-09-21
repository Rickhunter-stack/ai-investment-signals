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
 def test_total_return_split_only(self):
  m=[row("X","2026-01-01",100),row("X","2026-02-01",50,split=2)]
  self.assertAlmostEqual(o.total_return(m,date(2026,1,1),date(2026,2,1)),0)
 def test_total_return_reverse_split(self):
  m=[row("X","2026-01-01",10),row("X","2026-02-01",100,split=.1)]
  self.assertAlmostEqual(o.total_return(m,date(2026,1,1),date(2026,2,1)),0)
 def test_total_return_split_and_dividend(self):
  m=[row("X","2026-01-01",100),row("X","2026-02-01",50,div=1,split=2)]
  self.assertAlmostEqual(o.total_return(m,date(2026,1,1),date(2026,2,1)),.02)
 def test_t0_post_close_waits_for_later_session(self):
  captured=datetime(2026,9,21,21,30,tzinfo=timezone.utc)
  m={"NVDA":[row("NVDA","2026-09-21",100,"2026-09-22T21:00:00+00:00"),row("NVDA","2026-09-22",101,"2026-09-23T21:00:00+00:00")],
     "QQQ":[row("QQQ","2026-09-21",500,"2026-09-22T21:00:00+00:00"),row("QQQ","2026-09-22",501,"2026-09-23T21:00:00+00:00")]}
  self.assertEqual(o.t0_row(m,"NVDA","QQQ",captured,"2026-09-21")[0],date(2026,9,22))
 def test_t0_never_uses_pre_boundary_admitted_row(self):
  captured=datetime(2026,11,27,18,30,tzinfo=timezone.utc)
  m={"NVDA":[row("NVDA","2026-11-25",100,"2026-11-27T17:00:00+00:00"),row("NVDA","2026-11-30",101,"2026-12-01T21:00:00+00:00")],
     "QQQ":[row("QQQ","2026-11-25",500,"2026-11-27T17:00:00+00:00"),row("QQQ","2026-11-30",501,"2026-12-01T21:00:00+00:00")]}
  self.assertEqual(o.t0_row(m,"NVDA","QQQ",captured,"2026-11-27")[0],date(2026,11,30))
 def test_t0_requires_strictly_later_than_boundary(self):
  captured=datetime(2026,11,27,18,30,tzinfo=timezone.utc)
  m={"NVDA":[row("NVDA","2026-11-27",100,"2026-11-28T17:00:00+00:00"),row("NVDA","2026-11-30",101,"2026-12-01T21:00:00+00:00")],
     "QQQ":[row("QQQ","2026-11-27",500,"2026-11-28T17:00:00+00:00"),row("QQQ","2026-11-30",501,"2026-12-01T21:00:00+00:00")]}
  self.assertEqual(o.t0_row(m,"NVDA","QQQ",captured,"2026-11-27")[0],date(2026,11,30))
 def test_t0_excessive_drift_is_unavailable(self):
  snap={"date":"2026-09-21","captured_at":"2026-09-21T21:00:00+00:00","frozen":True,"method_version":"weekly-v1.0",
        "t0_after_session":{"NVDA":"2026-09-21"},"scores":{"NVDA":{"signal_score":80}}}
  m={"NVDA":[row("NVDA","2026-10-02",101,"2026-10-03T21:00:00+00:00")],
     "QQQ":[row("QQQ","2026-10-02",501,"2026-10-03T21:00:00+00:00")]}
  got=o.build_rows([snap],m,datetime(2026,10,4,tzinfo=timezone.utc))
  self.assertEqual(got[0]["status"],"unavailable")
  self.assertEqual(got[0]["unavailable_reason"],"t0_delay_exceeded")
 def test_gap_metadata_marks_return_window_incomplete(self):
  rows=[row("NVDA","2026-09-22",100),row("NVDA","2026-09-29",101)]
  rows[1]["gap_sessions"]=["2026-09-25"]
  self.assertTrue(o.gap_in_window(rows,date(2026,9,22),date(2026,9,29)))

 def test_quality_flag_only_invalidates_overlapping_interval(self):
  rows=[row("NVDA","2026-10-20",100),row("NVDA","2026-10-27",101),row("NVDA","2026-11-27",102)]
  rows[0]["quality_flags"]=[{"session_date":"2026-10-20","affected_from":"2026-10-19","affected_through":"2026-10-20"}]
  self.assertFalse(o.gap_in_window(rows,date(2026,10,27),date(2026,11,27)))
 def test_quality_flag_invalidates_when_t0_is_affected_prior_session(self):
  rows=[row("NVDA","2026-10-20",100),row("NVDA","2026-11-20",102)]
  rows[0]["quality_flags"]=[{"session_date":"2026-10-21","affected_from":"2026-10-20","affected_through":"2026-10-21"}]
  self.assertTrue(o.gap_in_window(rows,date(2026,10,20),date(2026,11,20)))

 def test_append_never_rewrites(self):
  old=[{"outcome_id":"A","excess_return":.1}]; new=[{"outcome_id":"A","excess_return":9.9},{"outcome_id":"B"}]
  got=o.append_unique(old,new); self.assertEqual(got[0]["excess_return"],.1); self.assertEqual(len(got),2)
 def test_pre_protocol_snapshot_excluded(self):
  snaps=[{"date":"2026-09-14","captured_at":"2026-09-14T21:00:00+00:00","frozen":True,"method_version":"weekly-v1.0","scores":{"NVDA":{"signal_score":80}}}]
  self.assertEqual(o.build_rows(snaps,{},datetime(2027,1,1,tzinfo=timezone.utc)),[])
if __name__=="__main__": unittest.main()
