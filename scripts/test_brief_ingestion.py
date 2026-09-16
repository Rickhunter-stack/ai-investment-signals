import json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import ingest_brief_events as mod
from test_brief_events import event

class IngestionTests(unittest.TestCase):
    def test_appends_without_rewriting_existing_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); first=event(); (root/"2026-09.json").write_text(json.dumps([first]),encoding="utf-8")
            second=event("EVT-20260916-0002","2026-09-16T20:00:00+00:00")
            with patch.object(mod,"DATA_DIR",root): mod.ingest([second])
            saved=json.loads((root/"2026-09.json").read_text(encoding="utf-8")); self.assertEqual(saved,[first,second])
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
