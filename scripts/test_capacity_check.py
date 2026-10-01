"""--check is mandatory before any write and never writes anything."""
import hashlib, json, subprocess, sys, unittest
from datetime import timedelta
from pathlib import Path
import append_capacity_observations as app
from test_capacity_monitor import Root, TUE, project, demand

SCRIPT=Path(__file__).resolve().parent/"append_capacity_observations.py"

def tree(root):
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob("*")) if p.is_file()}

class CapacityCheckTests(unittest.TestCase):
    def setUp(self): self.r=Root()
    def tearDown(self): self.r.tmp.cleanup()

    def test_check_writes_nothing_valid_or_invalid(self):
        before=tree(self.r.root)
        self.assertEqual(app.check([project(),demand()],self.r.root,now=TUE)[0],0)
        bad=project(); bad["ladder_level"]="C9"
        self.assertEqual(app.check([bad],self.r.root,now=TUE)[0],1)
        self.assertEqual(tree(self.r.root),before)

    def test_cli_check_writes_nothing_and_sets_exit_codes(self):
        drafts=self.r.root/"drafts.json"; drafts.write_text(json.dumps([project()]))
        before=tree(self.r.root)
        ok=subprocess.run([sys.executable,str(SCRIPT),str(drafts),"--check","--root",str(self.r.root)],capture_output=True,text=True)
        self.assertEqual(ok.returncode,0,ok.stderr); self.assertIn("--checked",ok.stdout)
        drafts.write_text(json.dumps([{"kind":"project"}])); before=tree(self.r.root)
        ko=subprocess.run([sys.executable,str(SCRIPT),str(drafts),"--check","--root",str(self.r.root)],capture_output=True,text=True)
        self.assertEqual(ko.returncode,1); self.assertIn("ERREURS BLOQUANTES",ko.stdout)
        self.assertEqual(tree(self.r.root),before)

    def test_all_blocking_errors_are_listed_at_once(self):
        a=project("a"); a["ladder_level"]="C5"            # C5 without commissioned_at
        b=project("b"); b["source"]={"url":"ftp://x"}       # invalid source
        c=project("c"); c["observed_at"]="2026-01-01T00:00:00+00:00"  # may not backdate
        code,report=app.check([a,b,c],self.r.root,now=TUE)
        self.assertEqual(code,1)
        for n in ("#1","#2","#3"): self.assertIn(f"draft {n}",report)

    def test_incomplete_information_is_a_warning_not_an_error(self):
        code,report=app.check([project("u",level="UNKNOWN"),project("g",unit="H100_units",value=1000),
                               project("d",level="C3",year=None)],self.r.root,now=TUE)
        self.assertEqual(code,0)
        for w in ("niveau UNKNOWN","hors GW_IT/MW_IT","non datée","dépendances non documentées"): self.assertIn(w,report)

    def test_report_is_project_by_project_and_keeps_nulls_visible(self):
        code,report=app.check([project("campus:a","C3",300,unit="MW_IT")],self.r.root,now=TUE)
        self.assertEqual(code,0)
        self.assertIn("campus:a · C3 (committed) · 300 MW_IT = 0.3 GW_IT / 300 MW_IT · millésime 2027",report)
        self.assertIn("null [no demand estimate]",report)

    def test_write_requires_the_digest_of_a_clean_check(self):
        drafts=[project()]
        with self.assertRaises(ValueError): app.append(drafts,self.r.root,now=TUE)
        digest=app.prepare(drafts,self.r.root,now=TUE)["digest"]
        with self.assertRaises(ValueError): app.append([project(value=2.0)],self.r.root,now=TUE,checked=digest)
        with self.assertRaises(ValueError): app.append(drafts,self.r.root,now=TUE,historical_seed=True,checked=digest)
        self.assertEqual(len(app.append(drafts,self.r.root,now=TUE,checked=digest)),1)
        # the journal changed: the old digest is stale
        with self.assertRaises(ValueError): app.append(drafts,self.r.root,now=TUE+timedelta(hours=1),checked=digest)

if __name__=="__main__": unittest.main()
