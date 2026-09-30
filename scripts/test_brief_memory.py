import json, tempfile, unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
import append_brief_memory as mod
import validate_brief_memory as v

LEGACY=json.loads((Path(__file__).resolve().parents[1]/"data/brief_memory.json").read_text(encoding="utf-8"))[:2]
NOW=datetime(2026,10,5,20,0,tzinfo=timezone.utc)

def brief(day="2026-10-04"):
    return {"date":day,"summary":"Semaine de confirmation.","stance":"constructif","themes":["ai_infrastructure"],
            "tickers":["NVDA"],"watch_next":"Capex hyperscalers.","invalidation":"Baisse du capex.","frozen":True}

class BriefMemoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.path=Path(self.tmp.name)/"brief_memory.json"
        self.path.write_text(json.dumps(LEGACY,ensure_ascii=False),encoding="utf-8")
        self.patch=patch.object(mod,"MEMORY",self.path); self.patch.start()
    def tearDown(self): self.patch.stop(); self.tmp.cleanup()
    def saved(self): return json.loads(self.path.read_text(encoding="utf-8"))

    def test_current_repository_memory_is_valid(self):
        self.assertEqual(v.validate_history(json.loads(v.MEMORY.read_text(encoding="utf-8"))),len(json.loads(v.MEMORY.read_text(encoding="utf-8"))))
    def test_appends_validated_brief_without_touching_legacy(self):
        record=mod.append(brief(),"2026-10-05T18:00:00+00:00",NOW)
        saved=self.saved()
        self.assertEqual(saved[:2],LEGACY); self.assertEqual(saved[2],record)
        self.assertEqual(record["validation"],"explicit_user_approval")
        self.assertEqual(record["archived_at"],NOW.isoformat()); self.assertTrue(record["frozen"])
    def test_rejects_duplicate_date(self):
        mod.append(brief(),"2026-10-05T18:00:00+00:00",NOW)
        with self.assertRaises(ValueError): mod.append(brief(),"2026-10-05T19:00:00+00:00",NOW)
        self.assertEqual(len(self.saved()),3)
    def test_rejects_backfill_of_pre_activation_brief(self):
        with self.assertRaises(ValueError): mod.append(brief("2026-09-27"),"2026-10-05T18:00:00+00:00",NOW)
        self.assertEqual(self.saved(),LEGACY)
    def test_rejects_out_of_order_brief(self):
        mod.append(brief("2026-10-11"),"2026-10-11T18:00:00+00:00",datetime(2026,10,12,tzinfo=timezone.utc))
        with self.assertRaises(ValueError): mod.append(brief("2026-10-04"),"2026-10-05T18:00:00+00:00",datetime(2026,10,12,tzinfo=timezone.utc))
    def test_rejects_unfrozen_entry(self):
        bad=brief(); bad["frozen"]=False
        with self.assertRaises(ValueError): mod.append(bad,"2026-10-05T18:00:00+00:00",NOW)
    def test_entry_cannot_carry_its_own_validation(self):
        bad=brief(); bad["validated_at"]="2026-10-05T18:00:00+00:00"
        with self.assertRaises(ValueError): mod.append(bad,"2026-10-05T18:00:00+00:00",NOW)
    def test_validation_must_follow_brief_and_not_be_in_future(self):
        with self.assertRaises(ValueError): mod.append(brief(),"2026-10-03T18:00:00+00:00",NOW)
        with self.assertRaises(ValueError): mod.append(brief(),"2026-10-06T18:00:00+00:00",NOW)
        with self.assertRaises(ValueError): mod.append(brief(),"2026-10-05T18:00:00",NOW)
    def test_history_rejects_rewritten_or_unvalidated_entries(self):
        with self.assertRaises(ValueError): v.validate_history([LEGACY[1],LEGACY[0]])
        with self.assertRaises(ValueError): v.validate_history(LEGACY+[brief()])
        edited=json.loads(json.dumps(LEGACY)); edited[1]["frozen"]=False
        with self.assertRaises(ValueError): v.validate_history(edited)
if __name__=="__main__": unittest.main()
