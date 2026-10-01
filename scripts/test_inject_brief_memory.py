import json, re, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import inject_brief_memory as mod

PAGE='<html><body><main><section class="card readcard"><h3>x</h3></section></main></body></html>'
EVENT={"event_id":"EVT-1","captured_at":"2026-09-25T08:00:00+02:00","title":"T</script><b>","factual_summary":"S",
       "type":"FACT","story":{"relation":"NEW"},"companies":["A"],"tickers":["AA"],"sources":[{"url":"https://example.com"}]}

class InjectBriefMemoryTests(unittest.TestCase):
    def run_twice(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/"events").mkdir(); (root/"events/2026-09-25.json").write_text(json.dumps([EVENT]))
            index=root/"index.html"; index.write_text(PAGE)
            with patch.object(mod,"INDEX",index),patch.object(mod,"BRIEF_EVENTS",root/"events"): mod.main(); mod.main()
            return index.read_text()

    def test_card_uses_brief_event_v1_type_and_relation(self):
        self.assertIn('data-classification="FACT"',self.run_twice()); self.assertIn("FACT · NEW",self.run_twice())

    def test_full_archive_embedded_once_and_safely(self):
        page=self.run_twice()
        self.assertEqual(page.count('id="aisSignalEvents"'),1); self.assertEqual(page.count("function filterBriefs"),1)
        raw=re.search(r'<script id="aisSignalEvents" type="application/json">(.*?)</script>',page,re.S).group(1)
        rows=json.loads(raw)
        self.assertEqual((rows[0]["type"],rows[0]["relation"],rows[0]["title"]),("FACT","NEW","T</script><b>"))

if __name__=="__main__": unittest.main()
