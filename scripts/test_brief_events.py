import copy
import unittest

from validate_brief_events import validate_append_only, validate_event, validate_journal


def event(event_id="EVT-20260916-0001", captured="2026-09-16T19:00:00+00:00"):
    return {
        "schema_version": "brief-event-v1",
        "event_id": event_id,
        "captured_at": captured,
        "published_at": "2026-09-16T12:00:00+00:00",
        "title": "HBM capacity signal",
        "factual_summary": "A sourced factual development relevant to AI infrastructure capacity.",
        "type": "WEAK_SIGNAL",
        "theme": "AI",
        "subtheme": "HBM_MEMORY",
        "companies": ["Micron"],
        "tickers": ["MU"],
        "sector": "Semiconductors",
        "sources": [{"url": "https://example.com/source", "source_name": "Example"}],
        "direction": "positive",
        "horizon": "medium",
        "importance": 80,
        "novelty": 75,
        "confidence": 85,
        "execution_risk": 30,
        "pricing_status": "partially_priced",
        "story": {"story_id": "STORY-HBM-001", "relation": "NEW"},
        "thesis": {"thesis_ids": [], "statement": "AI memory bottlenecks may capture more value."},
        "frozen": True,
    }


class BriefEventTests(unittest.TestCase):
    def test_valid_event(self):
        validate_event(event())

    def test_append_is_allowed(self):
        first = event()
        second = event("EVT-20260916-0002", "2026-09-16T20:00:00+00:00")
        validate_append_only([first], [first, second])

    def test_edit_is_rejected(self):
        first = event()
        changed = copy.deepcopy(first)
        changed["novelty"] = 99
        with self.assertRaises(ValueError):
            validate_append_only([first], [changed])

    def test_deletion_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_append_only([event()], [])

    def test_duplicate_id_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_journal([event(), event(captured="2026-09-16T20:00:00+00:00")])

    def test_confirmation_requires_story_id(self):
        item = event()
        item["story"] = {"story_id": None, "relation": "CONFIRM"}
        with self.assertRaises(ValueError):
            validate_event(item)

    def test_unfrozen_event_is_rejected(self):
        item = event()
        item["frozen"] = False
        with self.assertRaises(ValueError):
            validate_event(item)


if __name__ == "__main__":
    unittest.main()
