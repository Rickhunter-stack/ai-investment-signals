"""Validate append-only brief-event journals.

The journal is the prospective source of truth. Existing events are immutable:
new ingestion may only append events to the end of a monthly file.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "brief_events"
SCHEMA_VERSION = "brief-event-v1"
EVENT_ID = re.compile(r"^EVT-[0-9]{8}-[A-Z0-9]{4,12}$")
TICKER = re.compile(r"^[A-Z0-9.^-]+$")
ENUMS = {
    "type": {"FACT", "WEAK_SIGNAL", "HYPOTHESIS"},
    "direction": {"positive", "negative", "neutral"},
    "horizon": {"short", "medium", "long"},
    "pricing_status": {"not_priced", "partially_priced", "priced", "uncertain"},
}
RELATIONS = {"NEW", "REPEAT", "CONFIRM", "ACCELERATE", "DETERIORATE", "CONTRADICT", "RESOLVE"}
SCORES = ("importance", "novelty", "confidence", "execution_risk")
REQUIRED = {
    "schema_version", "event_id", "captured_at", "published_at", "title", "factual_summary",
    "type", "theme", "subtheme", "companies", "tickers", "sector", "sources", "direction",
    "horizon", "importance", "novelty", "confidence", "execution_risk", "pricing_status",
    "story", "thesis", "frozen",
}


def iso_datetime(value, nullable=False):
    if value is None and nullable:
        return
    if not isinstance(value, str):
        raise ValueError("datetime must be a string")
    datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate_event(event):
    if not isinstance(event, dict) or set(event) != REQUIRED:
        raise ValueError("event fields do not match brief-event-v1")
    if event["schema_version"] != SCHEMA_VERSION or event["frozen"] is not True:
        raise ValueError("event must be brief-event-v1 and frozen")
    if not EVENT_ID.fullmatch(event["event_id"]):
        raise ValueError("invalid event_id")
    iso_datetime(event["captured_at"])
    iso_datetime(event["published_at"], nullable=True)
    for field in ("title", "factual_summary", "theme", "subtheme", "sector"):
        if not isinstance(event[field], str) or not event[field].strip():
            raise ValueError(f"{field} is required")
    for field, allowed in ENUMS.items():
        if event[field] not in allowed:
            raise ValueError(f"invalid {field}")
    for field in SCORES:
        value = event[field]
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 100:
            raise ValueError(f"{field} must be an integer from 0 to 100")
    for field in ("companies", "tickers"):
        values = event[field]
        if not isinstance(values, list) or len(values) != len(set(values)):
            raise ValueError(f"{field} must be a unique array")
    if any(not isinstance(t, str) or not TICKER.fullmatch(t) for t in event["tickers"]):
        raise ValueError("invalid ticker")
    sources = event["sources"]
    if not isinstance(sources, list) or not sources:
        raise ValueError("at least one source is required")
    for source in sources:
        if set(source) - {"url", "source_name", "source_type"} or not {"url", "source_name"} <= set(source):
            raise ValueError("invalid source fields")
        parsed = urlparse(source["url"])
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or not source["source_name"].strip():
            raise ValueError("source must have a valid HTTP(S) URL and name")
    story = event["story"]
    if not isinstance(story, dict) or set(story) != {"story_id", "relation"} or story["relation"] not in RELATIONS:
        raise ValueError("invalid story")
    if story["relation"] != "NEW" and not story["story_id"]:
        raise ValueError("non-NEW story relation requires story_id")
    thesis = event["thesis"]
    if not isinstance(thesis, dict) or set(thesis) != {"thesis_ids", "statement"}:
        raise ValueError("invalid thesis")
    if not isinstance(thesis["thesis_ids"], list) or len(thesis["thesis_ids"]) != len(set(thesis["thesis_ids"])):
        raise ValueError("thesis_ids must be a unique array")


def validate_journal(events):
    if not isinstance(events, list):
        raise ValueError("journal must be an array")
    seen = set()
    previous = ""
    for event in events:
        validate_event(event)
        if event["event_id"] in seen:
            raise ValueError("duplicate event_id")
        if event["captured_at"] < previous:
            raise ValueError("events must be ordered by captured_at")
        seen.add(event["event_id"])
        previous = event["captured_at"]


def validate_append_only(previous, current):
    """Reject edits, deletion or reordering of already-frozen events."""
    validate_journal(previous)
    validate_journal(current)
    if len(current) < len(previous) or current[: len(previous)] != previous:
        raise ValueError("brief-event history is append-only; frozen events cannot change")


def main():
    paths = sorted(DATA_DIR.glob("????-??.json"))
    for path in paths:
        events = json.loads(path.read_text(encoding="utf-8"))
        validate_journal(events)
        for event in events:
            if event["captured_at"][:7] != path.stem:
                raise ValueError(f"{event['event_id']} belongs in {event['captured_at'][:7]}.json")
    print(f"Validated {len(paths)} brief-event journal(s)")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"brief-event validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
