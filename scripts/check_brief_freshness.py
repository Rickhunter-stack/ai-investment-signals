"""Fail when no brief event has been captured in main recently.

The daily brief can fail silently (a connector write blocked, a journal left
on an unmerged branch). This check makes that visible within a day.
"""
from __future__ import annotations
import json, sys
from datetime import datetime, timedelta, timezone
from validate_brief_events import DATA_DIR, parse_dt

DEFAULT_MAX_AGE_HOURS = 24

def latest_capture(data_dir=DATA_DIR):
    latest = None
    for path in sorted(data_dir.glob("*.json")):
        for event in json.loads(path.read_text(encoding="utf-8")):
            captured = parse_dt(event["captured_at"])
            if latest is None or captured > latest[0]: latest = (captured, event["event_id"], path.name)
    return latest

def check(now=None, max_age_hours=DEFAULT_MAX_AGE_HOURS, data_dir=DATA_DIR):
    now = now or datetime.now(timezone.utc)
    latest = latest_capture(data_dir)
    if latest is None: return False, "no brief event found in data/brief_events"
    captured, event_id, name = latest
    age = now - captured
    hours = age.total_seconds() / 3600
    message = f"latest brief event {event_id} ({name}) captured at {captured.isoformat()}, {hours:.1f} h ago"
    return age <= timedelta(hours=max_age_hours), message

def main():
    max_age = float(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_MAX_AGE_HOURS
    ok, message = check(max_age_hours=max_age)
    if not ok:
        print(f"brief freshness failed: {message} (limit {max_age:g} h)", file=sys.stderr); raise SystemExit(1)
    print(f"Brief journal is fresh: {message}")
if __name__ == "__main__":
    main()
