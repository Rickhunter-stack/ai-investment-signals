"""Isolation invariants: no arrow from the Capacity Monitor to the Signal Score."""
import ast, hashlib, json, re, shutil, tempfile, unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
import capacity_common as cc
import append_capacity_observations as app
import compute_capacity_snapshot as comp
import validate_signal_research_isolation as iso
import check_append_only_git as guard

REPO=Path(__file__).resolve().parents[1]
CAPACITY_CODE=["scripts/capacity_common.py","scripts/append_capacity_observations.py","scripts/compute_capacity_snapshot.py","scripts/validate_capacity.py"]
PROTOCOL_CODE=["scripts/generate_weekly_signals.py","scripts/compute_outcomes.py","src/market.py","scripts/build_static_dashboard.py",
               "scripts/freeze_fundamentals_pit.py","scripts/collect_fundamentals.py","scripts/inject_brief_memory.py","run.py"]
PROTECTED=["data/weekly_signals.json","data/signal_research.json","data/outcomes_v1.json","data/fundamentals.json","data/universe_seed.csv",
           "data/brief_memory.json","data/veille.db","PREREGISTRATION.md","config/scoring.yaml"]
PROTECTED_DIRS=["data/market_pit","data/fundamentals_pit","data/brief_events"]

def strings(path):
    return [n.value for n in ast.walk(ast.parse((REPO/path).read_text(encoding="utf-8"))) if isinstance(n,ast.Constant) and isinstance(n.value,str)]

class CapacityIsolationTests(unittest.TestCase):
    def test_signal_protocol_code_never_references_capacity(self):
        for path in PROTOCOL_CODE:
            tree=ast.parse((REPO/path).read_text(encoding="utf-8"))
            names=[a.name for n in ast.walk(tree) if isinstance(n,(ast.Import,ast.ImportFrom)) for a in n.names]+[n.module or "" for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
            self.assertFalse([x for x in names if "capacity" in x.lower()],path)
            self.assertFalse([s for s in strings(path) if "data/capacity" in s or "config/capacity" in s or "capacity_monitor" in s],path)

    def test_capacity_code_only_names_its_own_data_and_the_weekly_wall(self):
        allowed={"data/weekly_signals.json"}
        for path in CAPACITY_CODE:
            for s in strings(path):
                for p in PROTECTED+PROTECTED_DIRS:
                    if p in s: self.assertIn(p,allowed,f"{path} names {p}")

    def test_full_capacity_pipeline_writes_only_under_data_capacity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for p in PROTECTED:
                if (REPO/p).exists(): (root/p).parent.mkdir(parents=True,exist_ok=True); shutil.copy(REPO/p,root/p)
            for d in PROTECTED_DIRS: shutil.copytree(REPO/d,root/d)
            (root/"config/capacity").mkdir(parents=True)
            shutil.copy(REPO/"config/capacity/definitions_capacity_monitor_v0.1.json",root/"config/capacity/")
            (root/"data/capacity/observations").mkdir(parents=True); (root/"data/capacity/snapshots.json").write_text("[]\n")
            def digest():
                return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob("*")) if p.is_file()}
            before=digest()
            last=max(datetime.fromisoformat(s["captured_at"]) for s in json.loads((root/"data/weekly_signals.json").read_text()) if s.get("captured_at"))
            at=last+timedelta(hours=1)
            drafts=[{"kind":"assessment","component":"E","node":"power","value":"LOW","justification":"x","source":{"url":"https://example.com"}}]
            app.append(drafts,root,now=at,checked=app.prepare(drafts,root,now=at)["digest"])
            comp.write(comp.build(root,now=at+timedelta(hours=1)),root)
            after=digest()
            changed={k for k in set(before)|set(after) if before.get(k)!=after.get(k)}
            self.assertTrue(changed)
            self.assertTrue(all(k.startswith("data/capacity/") for k in changed),changed)

    def test_signal_research_may_not_cite_capacity_outputs(self):
        self.assertEqual(iso.violations(json.loads((REPO/"data/signal_research.json").read_text(encoding="utf-8"))),[])
        bad={"NVDA":{"pricing_headroom":{"score":40,"rationale":"x","sources":["https://ai-investment-signals.vercel.app/data/capacity/snapshots.json"]},
                     "execution_risk":{"score":40,"rationale":"Absorption stress eleve","sources":["https://example.com"]}}}
        self.assertEqual(len(iso.violations(bad)),2)

    def test_definitions_are_non_scoring_and_uncalibrated(self):
        d,_=cc.load_definitions(REPO)
        self.assertEqual((d["scoring_use"],d["aggregate_score"],d["commitment_weights"],d["absorption_stress"]["automatic_thresholds"]),("none",None,None,None))
        self.assertEqual({k for k,v in d["components"].items() if v["type"]=="qualitative"},{"E","F"})

    def test_frontend_reads_only_capacity_data_and_shows_banner(self):
        js=(REPO/"capacity.js").read_text(encoding="utf-8")
        self.assertEqual(re.findall(r"fetch\('([^']+)'",js),["/data/capacity/snapshots.json"])
        self.assertIn("SHADOW MODEL — EXPERIMENTAL — NON SCORING",js); self.assertIn("Not used in the Signal Score",js)
        for shared in ("AIS_FUND","AIS_BRIEF_ARCHIVE","SIGNAL_HISTORY","ROWS","byTicker"): self.assertNotIn(shared,js)

    def test_append_only_guard_covers_capacity(self):
        self.assertIn("data/capacity/snapshots.json",guard.tracked_paths("HEAD"))
        self.assertIn("data/capacity/observations",(REPO/"scripts/check_append_only_git.py").read_text())

if __name__=="__main__": unittest.main()
