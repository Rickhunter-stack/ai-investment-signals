import copy, json, shutil, tempfile, unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
import capacity_common as cc
import append_capacity_observations as app
import compute_capacity_snapshot as comp
import validate_capacity as val

REPO=Path(__file__).resolve().parents[1]
MON=datetime(2026,10,5,23,40,tzinfo=timezone.utc)   # weekly freeze N
TUE=MON+timedelta(days=1)
SUN=MON+timedelta(days=6)

def weekly(date,captured,sha): return {"date":date,"frozen":True,"captured_at":captured.isoformat(),"input_sha256":{"research":sha,"fundamentals":"f"},"scores":{}}

def project(asset="campus:a",level="C3",value=1.0,unit="GW_IT",year=2027,**kw):
    d={"kind":"project","asset_id":asset,"name":asset,"asset_class":"datacenter","ladder_level":level,
       "level_evidence":"evidence for "+level,"capacity":{"value":value,"unit":unit},"expected_operational_year":year,
       "dependencies_documented":False,"source":{"url":"https://example.com/"+asset,"published_at":"2026-09-15T00:00:00+00:00"}}
    d.update(kw); return d

def demand(scenario="base",year=2027,value=2.0,series="iea",unit="GW_IT"):
    return {"kind":"demand","series_id":series,"scenario":scenario,"year":year,"value":value,"unit":unit,
            "method_note":"independent demand","source":{"url":"https://example.com/d","published_at":None}}

def assessment(component="E",value="LOW",node="power",**kw):
    d={"kind":"assessment","component":component,"node":node,"value":value,"justification":"why","source":{"url":"https://example.com/e"}}
    d.update(kw); return d

class Root:
    def __init__(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name)
        (self.root/"config/capacity").mkdir(parents=True); (self.root/"data/capacity/observations").mkdir(parents=True)
        shutil.copy(REPO/"config/capacity/definitions_capacity_monitor_v0.1.json",self.root/"config/capacity/")
        (self.root/"data/capacity/snapshots.json").write_text("[]\n")
        self.weekly=[weekly("2026-09-29",datetime(2026,9,29,2,38,tzinfo=timezone.utc),"sha-n-1"),weekly("2026-10-05",MON,"sha-n")]
        self.save_weekly()
    def save_weekly(self): (self.root/"data/weekly_signals.json").write_text(json.dumps(self.weekly))
    def add(self,drafts,at,**kw): return app.append(drafts,self.root,now=at,**kw)
    def snap(self,at):
        s=comp.build(self.root,now=at)
        if s: comp.write(s,self.root)
        return s

class CapacityMonitorTests(unittest.TestCase):
    def setUp(self): self.r=Root()
    def tearDown(self): self.r.tmp.cleanup()

    def test_append_sets_pit_fields_and_wall_reference(self):
        row=self.r.add([project()],TUE)[0]
        self.assertEqual(row["observed_at"],TUE.isoformat()); self.assertEqual(row["weekly_snapshot_date"],"2026-10-05")
        self.assertEqual(row["method_version"],"capacity_monitor_v0.1"); self.assertIs(row["frozen"],True); self.assertIs(row["historical_seed"],False)
        self.assertEqual(row["source"]["published_at"],"2026-09-15T00:00:00+00:00")

    def test_drafts_cannot_backdate_or_set_pit_fields(self):
        for f,v in (("observed_at","2026-09-15T00:00:00+00:00"),("weekly_snapshot_date","2026-09-29"),("historical_seed",False)):
            with self.assertRaises(ValueError): self.r.add([project(**{f:v})],TUE)

    def test_source_published_after_ingestion_is_rejected(self):
        bad=project(); bad["source"]["published_at"]="2026-10-07T00:00:00+00:00"
        with self.assertRaises(ValueError): self.r.add([bad],TUE)

    def test_historical_seed_keeps_ingestion_time(self):
        row=self.r.add([project()],TUE,historical_seed=True)[0]
        self.assertTrue(row["historical_seed"]); self.assertEqual(row["observed_at"],TUE.isoformat())
        self.assertEqual(self.r.snap(SUN)["counts"]["historical_seed"],1)

    def test_no_wall_no_observation(self):
        self.r.weekly=[]; self.r.save_weekly()
        with self.assertRaises(ValueError): self.r.add([project()],TUE)

    def test_snapshot_references_latest_weekly_freeze(self):
        s=self.r.snap(SUN)
        self.assertEqual((s["weekly_snapshot_date"],s["weekly_research_sha256"]),("2026-10-05","sha-n"))
        self.assertEqual(s["weekly_snapshot_captured_at"],MON.isoformat())
        self.assertLess(datetime.fromisoformat(s["weekly_snapshot_captured_at"]),datetime.fromisoformat(s["capacity_snapshot_captured_at"]))
        self.assertIsNone(comp.build(self.r.root,now=SUN+timedelta(hours=1)))

    def test_later_observation_never_changes_earlier_state(self):
        self.r.add([project(value=1.0)],TUE)
        definitions,sha=cc.load_definitions(self.r.root); ref=cc.wall_ref(cc.weekly_refs(self.r.root),SUN)
        before=cc.compute(definitions,sha,cc.load_observations(self.r.root),SUN,ref)
        self.r.add([project(value=5.0,level="C4")],SUN+timedelta(hours=2))
        self.assertEqual(cc.compute(definitions,sha,cc.load_observations(self.r.root),SUN,ref),before)

    def test_stored_snapshot_is_reproducible_and_tampering_detected(self):
        self.r.add([project(),demand()],TUE); self.r.snap(SUN)
        self.assertEqual(val.validate(self.r.root),(2,1))
        path=self.r.root/"data/capacity/snapshots.json"; snaps=json.loads(path.read_text())
        snaps[0]["buildout"]["years"]["2027"]["committed_gw"]=99; path.write_text(json.dumps(snaps))
        with self.assertRaises(ValueError): val.validate(self.r.root)

    def test_definitions_cannot_change_after_use(self):
        self.r.snap(SUN)
        p=self.r.root/"config/capacity/definitions_capacity_monitor_v0.1.json"; d=json.loads(p.read_text()); d["years"].append(2031); p.write_text(json.dumps(d))
        with self.assertRaises(ValueError): val.validate(self.r.root)

    def test_supersedes_only_from_correction_time(self):
        first=self.r.add([project(asset="campus:wrong")],TUE)[0]
        self.r.add([project(asset="campus:right",supersedes=first["observation_id"])],TUE+timedelta(days=2))
        obs=cc.load_observations(self.r.root)
        early,_=cc.pit_state(obs,TUE+timedelta(days=1)); late,_=cc.pit_state(obs,SUN)
        self.assertIn(("project","campus:wrong"),early); self.assertNotIn(("project","campus:wrong"),late)
        self.assertIn(("project","campus:right"),late)

    def test_cancelled_project_stays_in_history_and_ladder(self):
        self.r.add([project(level="C3")],TUE); self.r.add([project(level="X")],TUE+timedelta(days=1))
        s=self.r.snap(SUN)
        self.assertEqual(s["ladder"]["X"]["projects"],1); self.assertEqual(s["buildout"]["years"]["2027"]["committed_gw"],0)
        self.assertEqual(len(s["input_observation_ids"]),2)

    def test_committed_operational_and_effective(self):
        self.r.add([project("a","C3",1.0),project("b","C4",2.0,dependencies_documented=True,dependency_evidence=["https://example.com/ppa"]),
                    project("c","C5",4.0,year=None,commissioned_at="2026-06-01"),project("d","C1",8.0)],TUE)
        y=self.r.snap(SUN)["buildout"]["years"]["2027"]
        self.assertEqual((y["announced_gw"],y["committed_gw"],y["operational_gw"],y["effective_gw"]),(15.0,7.0,4.0,6.0))

    def test_incomparable_units_give_null_never_estimates(self):
        self.r.add([project(unit="H100_units",value=100000),demand()],TUE)
        s=self.r.snap(SUN)
        self.assertIsNone(s["buildout"]["years"]["2027"]["effective_gw"])
        self.assertEqual(s["absorption_stress"]["2027"]["base"],{"value":None,"reason":"effective capacity unknown"})
        self.assertEqual(s["ladder"]["C3"]["non_canonical_projects"],1)

    def test_absorption_stress_ratio_and_null_rules(self):
        self.r.add([project("c","C5",3.0,year=None,commissioned_at="2026-01-01"),demand("base",2027,2.0),
                    demand("bull",2027,1.0,series="a"),demand("bull",2027,4.0,series="b")],TUE)
        a=self.r.snap(SUN)["absorption_stress"]["2027"]
        self.assertEqual(a["base"]["value"],1.5)
        self.assertEqual(a["bull"],{"value":None,"reason":"several demand series without declared reference"})
        self.assertEqual(a["bear"],{"value":None,"reason":"no demand estimate"})

    def test_depreciation_retires_capacity(self):
        self.r.add([project("c","C5",1.0,year=None,commissioned_at="2026-01-01",expected_useful_life_years=2),
                    project("d","C5",2.0,year=None,commissioned_at="2026-01-01")],TUE)
        s=self.r.snap(SUN)
        self.assertEqual([s["buildout"]["years"][y]["operational_gw"] for y in ("2026","2027","2028")],[3.0,3.0,2.0])
        self.assertEqual(s["buildout"]["depreciation_unknown_gw"],2.0)

    def test_qualitative_components_require_evidence(self):
        with self.assertRaises(ValueError): self.r.add([assessment("E","VERY_HIGH")],TUE)
        with self.assertRaises(ValueError): self.r.add([assessment("F","LOW")],TUE)
        with self.assertRaises(ValueError): self.r.add([assessment("C","LOW")],TUE)
        self.r.add([assessment("F","LOW",node="hyperscalers",relations=["Vendor financing: supplier invests in its customer"])],TUE)
        self.assertEqual(self.r.snap(SUN)["system_risk"]["F"][0]["value"],"LOW")

    def test_time_to_supply_uses_realized_dates_only(self):
        self.r.add([project("c","C5",1.0,year=None,commitment_date="2025-01-01",commissioned_at="2026-01-01"),
                    project("d","C3",1.0,commitment_date="2025-06-01")],TUE)
        t=self.r.snap(SUN)["system_risk"]["T"]
        self.assertEqual(t["realized_months"]["n"],1); self.assertAlmostEqual(t["realized_months"]["median"],12.0,places=0)
        self.assertEqual(t["expected_committed_gw_by_year"]["2027"],1.0)

    def test_snapshot_is_non_scoring_with_no_aggregate(self):
        s=self.r.snap(SUN)
        self.assertEqual(s["scoring_use"],"none")
        self.assertNotIn("score",json.dumps(s["system_risk"]).lower())

if __name__=="__main__": unittest.main()
