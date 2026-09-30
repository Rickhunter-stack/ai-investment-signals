"""Permanent end-to-end guard (amendment v1.3 C7).

Simulates several weeks of scheduled confirmatory collection through the real
collector admission path (_eligible_rows -> _admit_rows -> _append_journal) and
then runs the real outcome engine. A matured horizon must become `measured`.
This is the test that would have caught the weekly-cadence/gap deadlock where
every horizon froze as `market_gap_in_return_window`.
"""
import importlib.util, json, tempfile, unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
import exchange_calendars as xcals
import pandas as pd
import src.market as market

P=Path(__file__).parent/"compute_outcomes.py"; s=importlib.util.spec_from_file_location("o_e2e",P); o=importlib.util.module_from_spec(s); s.loader.exec_module(o)
CAL=xcals.get_calendar("XNYS")
TICKERS=list(market.CONFIRMATORY_SECURITIES)+list(market.BENCHMARK_TICKERS)

def vendor_response(observed,skip=()):
 """One-month daily response ending at the latest XNYS session opened by `observed`."""
 sessions=[s for s in CAL.sessions_in_range(pd.Timestamp(observed.date()-timedelta(days=30)),pd.Timestamp(observed.date()))
           if CAL.session_open(s)<=pd.Timestamp(observed) and s.date().isoformat() not in skip]
 idx=pd.DatetimeIndex([pd.Timestamp(s.date()) for s in sessions])
 frames={}
 for k,t in enumerate(TICKERS):
  close=[100+k+0.1*s.toordinal()%50 for s in idx]
  frames[t]=pd.DataFrame({"Close":close,"Adj Close":close,"Dividends":[0.0]*len(idx),"Stock Splits":[0.0]*len(idx)},index=idx)
 return pd.concat(frames,axis=1)

def collect(observed,skip=()):
 raw=vendor_response(observed,skip)
 obs=observed.isoformat()
 rows=(market._eligible_rows(raw[list(market.CONFIRMATORY_SECURITIES)],list(market.CONFIRMATORY_SECURITIES),obs,"security")
       +market._eligible_rows(raw[list(market.BENCHMARK_TICKERS)],list(market.BENCHMARK_TICKERS),obs,"benchmark"))
 for r in rows: r["run_id"]="sim"; r["commit_sha"]="sim"
 market._validate_confirmatory_rows(rows)
 return market._append_journal(market._admit_rows(rows,market._load_journal()))

def run_schedule(journal,days,cadence):
 with patch.object(market,"JOURNAL",journal):
  for d in days:
   if d.weekday() in cadence: collect(datetime(d.year,d.month,d.day,23,30,tzinfo=timezone.utc))

def snapshot():
 # Mirrors the real 2026-09-22 cohort: frozen Monday night, boundary = that Monday.
 return {"date":"2026-09-21","captured_at":"2026-09-21T23:45:00+00:00","frozen":True,"method_version":"weekly-v1.0",
         "t0_after_session":{t:"2026-09-21" for t in o.UNIVERSE},"scores":{t:{"signal_score":50.0} for t in o.UNIVERSE}}

def days(start,end):
 return [start+timedelta(days=i) for i in range((end-start).days+1)]

class OutcomeEndToEndTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.journal=Path(self.tmp.name)/"market_pit"
 def tearDown(self): self.tmp.cleanup()

 def outcomes(self,now):
  return o.build_rows([snapshot()],o.load_market(self.journal),now)

 def assert_m1_measured(self):
  rows=self.outcomes(datetime(2026,11,3,tzinfo=timezone.utc))
  t0={r["ticker"]:r for r in rows if r["outcome_id"].endswith(":T0")}
  m1={r["ticker"]:r for r in rows if r.get("horizon")=="M1"}
  self.assertEqual(set(t0),set(o.UNIVERSE))
  self.assertTrue(all(r["status"]=="anchored" and r["t0_date"]=="2026-09-22" for r in t0.values()))
  self.assertEqual(set(m1),set(o.UNIVERSE))
  self.assertEqual({r["status"] for r in m1.values()},{"measured"},[r.get("unavailable_reason") for r in m1.values()])
  return m1

 def test_weekly_cadence_with_catchup_yields_measured_outcome(self):
  run_schedule(self.journal,days(date(2026,9,14),date(2026,11,2)),cadence={0})
  m1=self.assert_m1_measured()
  self.assertEqual(m1["NVDA"]["measurement_date"],"2026-10-22")

 def test_daily_cadence_yields_measured_outcome(self):
  run_schedule(self.journal,days(date(2026,9,14),date(2026,11,2)),cadence={0,1,2,3,4})
  self.assert_m1_measured()

 def test_journal_is_contiguous_and_append_only_across_runs(self):
  with patch.object(market,"JOURNAL",self.journal):
   for d in days(date(2026,9,14),date(2026,10,12)):
    if d.weekday()==0:
     before=[json.loads(p.read_text()) for p in sorted(self.journal.glob("*.json"))] if self.journal.exists() else []
     collect(datetime(d.year,d.month,d.day,23,30,tzinfo=timezone.utc))
     after=[json.loads(p.read_text()) for p in sorted(self.journal.glob("*.json"))]
     for old,new in zip(before,after): self.assertEqual(new[:len(old)],old)
  rows=o.load_market(self.journal)["NVDA"]
  self.assertTrue(all(r["gap_sessions"]==[] and not r["gap_unbounded"] for r in rows))
  self.assertTrue(all(r["observed_at"]>r["session_date"] for r in rows))

 def test_catchup_rows_are_never_backdated(self):
  run_schedule(self.journal,days(date(2026,9,14),date(2026,9,29)),cadence={0})
  rows=[r for r in o.load_market(self.journal)["NVDA"] if r["admission"]=="catchup"]
  self.assertTrue(rows)
  for r in rows:
   self.assertIn(r["observed_at"][:10],{"2026-09-21","2026-09-28"})
   self.assertGreater(r["observed_at"][:10],r["session_date"])

 def test_vendor_missing_session_inside_window_makes_outcome_unavailable(self):
  with patch.object(market,"JOURNAL",self.journal):
   for d in days(date(2026,9,14),date(2026,11,2)):
    if d.weekday()==0: collect(datetime(d.year,d.month,d.day,23,30,tzinfo=timezone.utc),skip=("2026-10-07",))
  rows=self.outcomes(datetime(2026,11,3,tzinfo=timezone.utc))
  m1=[r for r in rows if r.get("horizon")=="M1"]
  self.assertTrue(m1)
  self.assertTrue(all(r["status"]=="unavailable" and r["unavailable_reason"]=="market_gap_in_return_window" for r in m1))

 def test_interruption_longer_than_window_is_not_reconstructed(self):
  schedule=[d for d in days(date(2026,9,14),date(2026,11,9)) if not date(2026,9,29)<=d<=date(2026,11,1)]
  run_schedule(self.journal,schedule,cadence={0})
  nvda=o.load_market(self.journal)["NVDA"]
  resumed=[r for r in nvda if r["gap_sessions"]]
  self.assertEqual(len(resumed),1); self.assertTrue(resumed[0]["gap_unbounded"])
  self.assertNotIn("2026-10-01",{r["session_date"] for r in nvda})
  rows=self.outcomes(datetime(2026,11,10,tzinfo=timezone.utc))
  self.assertTrue(all(r["status"]=="unavailable" for r in rows if r.get("horizon")=="M1"))

if __name__=="__main__": unittest.main()
