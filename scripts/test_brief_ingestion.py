import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import ingest_brief_events as mod


def event(event_id="EVT-20260917-ABCD", captured="2026-09-17T08:00:00+02:00"):
    return {
        "schema_version":"brief-event-v1","event_id":event_id,"captured_at":captured,
        "published_at":"2026-09-17T07:00:00+02:00","title":"Material AI infrastructure event",
        "factual_summary":"A sourced material event relevant to the prospective investment journal.",
        "type":"FACT","theme":"AI infrastructure","subtheme":"HBM","companies":["Example Corp"],
        "tickers":["EXM"],"sector":"Semiconductors","sources":[{"url":"https://example.com/source","source_name":"Example"}],
        "direction":"positive","horizon":"medium","importance":80,"novelty":75,"confidence":90,
        "execution_risk":30,"pricing_status":"uncertain","story":{"story_id":None,"relation":"NEW"},
        "thesis":{"thesis_ids":[],"statement":None},"frozen":True,
    }


class IngestionTests(unittest.TestCase):
    def test_appends_without_rewriting_existing_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); first=event(); (root/"2026-09.json").write_text(json.dumps([first]),encoding="utf-8")
            second=event("EVT-20260917-EFGH","2026-09-17T09:00:00+02:00")
            with patch.object(mod,"DATA_DIR",root): mod.ingest([second])
            saved=json.loads((root/"2026-09.json").read_text(encoding="utf-8"))
            self.assertEqual(saved[0],first); self.assertEqual(saved[1],second)

    def test_rejects_duplicate_event_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); first=event(); (root/"2026-09.json").write_text(json.dumps([first]),encoding="utf-8")
            with patch.object(mod,"DATA_DIR",root):
                with self.assertRaises(ValueError): mod.ingest([first])

    def test_rejects_invalid_event_before_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); bad=event(); bad["sources"]=[]
            with patch.object(mod,"DATA_DIR",root):
                with self.assertRaises(ValueError): mod.ingest([bad])
            self.assertFalse((root/"2026-09.json").exists())


if __name__=="__main__": unittest.main()
