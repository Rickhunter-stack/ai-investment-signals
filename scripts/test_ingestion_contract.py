import unittest
from pathlib import Path

class ContractTests(unittest.TestCase):
    def test_required_ingestion_files_exist(self):
        root=Path(__file__).resolve().parents[1]
        for rel in ["schemas/brief_event_v1.schema.json","scripts/validate_brief_events.py","scripts/ingest_brief_events.py","docs/DAILY_BRIEF_EVENT_PROMPT.md"]:
            self.assertTrue((root/rel).exists(),rel)

if __name__=="__main__": unittest.main()
