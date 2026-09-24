"""Append structured ChatGPT brief events to immutable daily journals."""
from __future__ import annotations
import json, sys
from pathlib import Path
from validate_brief_events import DATA_DIR, validate_append_only, validate_event

def load_input(path: Path):
    payload=json.loads(path.read_text(encoding="utf-8")); return payload if isinstance(payload,list) else [payload]

def ingest(events):
    if not events: return []
    for event in events: validate_event(event)
    grouped={}
    for event in events: grouped.setdefault(event["captured_at"][:10],[]).append(event)
    written=[]; DATA_DIR.mkdir(parents=True,exist_ok=True)
    for day, additions in grouped.items():
        path=DATA_DIR/f"{day}.json"; previous=json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
        existing={e["event_id"] for e in previous}; duplicates=existing.intersection(e["event_id"] for e in additions)
        if duplicates: raise ValueError(f"event_id already exists: {sorted(duplicates)}")
        current=previous+additions; validate_append_only(previous,current)
        tmp=path.with_suffix(".json.tmp"); tmp.write_text(json.dumps(current,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); tmp.replace(path)
        written.extend(e["event_id"] for e in additions)
    return written

def main():
    if len(sys.argv)!=2: raise SystemExit("usage: ingest_brief_events.py <events.json>")
    written=ingest(load_input(Path(sys.argv[1]))); print(f"Appended {len(written)} event(s)")
if __name__=="__main__":
    try: main()
    except (ValueError,json.JSONDecodeError) as exc:
        print(f"brief-event ingestion failed: {exc}",file=sys.stderr); raise SystemExit(1)
