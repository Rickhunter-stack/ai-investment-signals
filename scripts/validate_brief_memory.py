"""Validate the append-only weekly brief memory (docs/BRIEF_MEMORY.md)."""
from __future__ import annotations
import json, sys
from datetime import date, datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; MEMORY=ROOT/"data/brief_memory.json"
# The two entries written by hand before this protocol. They stay frozen as-is and
# are the only entries allowed to lack validation provenance. No other brief dated
# before ACTIVATION may ever be added (no backfill).
LEGACY_DATES=("2026-09-11","2026-09-20"); ACTIVATION=date(2026,9,30)
CONTENT_FIELDS={"date","summary","stance","themes","tickers","watch_next","invalidation","frozen"}
PROVENANCE_FIELDS={"validation","validated_at","archived_at"}
VALIDATION="explicit_user_approval"

def _aware(value,field):
    try: ts=datetime.fromisoformat(str(value).replace("Z","+00:00"))
    except ValueError as exc: raise ValueError(f"{field} must be an ISO timestamp") from exc
    if ts.tzinfo is None: raise ValueError(f"{field} must be timezone-aware")
    return ts

def validate_content(entry):
    if not isinstance(entry,dict): raise ValueError("brief memory entry must be an object")
    missing=CONTENT_FIELDS-set(entry)
    if missing: raise ValueError(f"missing fields: {sorted(missing)}")
    day=date.fromisoformat(entry["date"])
    if entry["frozen"] is not True: raise ValueError("frozen must be true")
    for f in ("summary","stance","watch_next","invalidation"):
        if not isinstance(entry[f],str) or not entry[f].strip(): raise ValueError(f"{f} must be a non-empty string")
    for f in ("themes","tickers"):
        if not isinstance(entry[f],list) or not all(isinstance(x,str) and x for x in entry[f]): raise ValueError(f"{f} must be a list of strings")
    return day

def validate_entry(entry):
    day=validate_content(entry)
    extra=set(entry)-CONTENT_FIELDS-PROVENANCE_FIELDS
    if extra: raise ValueError(f"unexpected fields: {sorted(extra)}")
    missing=PROVENANCE_FIELDS-set(entry)
    if missing: raise ValueError(f"{entry['date']}: missing validation provenance {sorted(missing)}")
    if entry["validation"]!=VALIDATION: raise ValueError(f"validation must be {VALIDATION!r}")
    if day<ACTIVATION: raise ValueError(f"{entry['date']}: briefs dated before {ACTIVATION} are not archived (no backfill)")
    validated=_aware(entry["validated_at"],"validated_at"); archived=_aware(entry["archived_at"],"archived_at")
    if validated.date()<day: raise ValueError("validated_at precedes the brief date")
    if archived<validated: raise ValueError("archived_at precedes validated_at")
    return day

def validate_history(entries):
    if not isinstance(entries,list): raise ValueError("brief memory must be a JSON array")
    legacy=[e.get("date") for e in entries[:len(LEGACY_DATES)] if isinstance(e,dict)]
    if tuple(legacy)!=LEGACY_DATES: raise ValueError("legacy brief memory entries changed or reordered")
    previous=None
    for i,entry in enumerate(entries):
        day=validate_content(entry) if i<len(LEGACY_DATES) else validate_entry(entry)
        if previous is not None and day<=previous: raise ValueError(f"{entry['date']}: dates must be unique and strictly increasing")
        previous=day
    return len(entries)

def main():
    print(f"brief memory validated: {validate_history(json.loads(MEMORY.read_text(encoding='utf-8')))} entries")
if __name__=="__main__":
    try: main()
    except (ValueError,json.JSONDecodeError) as exc:
        print(f"brief memory validation failed: {exc}",file=sys.stderr); raise SystemExit(1)
