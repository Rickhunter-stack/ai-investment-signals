"""Validate append-only brief-event journals."""
from __future__ import annotations
import json, re, sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]; DATA_DIR=ROOT/"data"/"brief_events"; SCHEMA_VERSION="brief-event-v1"
EVENT_ID=re.compile(r"^EVT-[0-9]{8}-[A-Z0-9]{4,12}$"); TICKER=re.compile(r"^[A-Z0-9.^-]+$")
ENUMS={"type":{"FACT","WEAK_SIGNAL","HYPOTHESIS"},"direction":{"positive","negative","neutral"},"horizon":{"short","medium","long"},"pricing_status":{"not_priced","partially_priced","priced","uncertain"}}
RELATIONS={"NEW","REPEAT","CONFIRM","ACCELERATE","DETERIORATE","CONTRADICT","RESOLVE"}; SCORES=("importance","novelty","confidence","execution_risk")
REQUIRED={"schema_version","event_id","captured_at","published_at","title","factual_summary","type","theme","subtheme","companies","tickers","sector","sources","direction","horizon","importance","novelty","confidence","execution_risk","pricing_status","story","thesis","frozen"}
# Events captured before this release remain valid exactly as frozen. New events must
# carry a publication timestamp, preventing ambiguous information-time T0.
PUBLICATION_REQUIRED_FROM=datetime.fromisoformat("2026-09-17T09:30:00+02:00")

def parse_dt(value, nullable=False):
    if value is None and nullable: return None
    if not isinstance(value,str): raise ValueError("datetime must be a string")
    dt=datetime.fromisoformat(value.replace("Z","+00:00"))
    if dt.tzinfo is None: raise ValueError("datetime must include timezone")
    return dt

def validate_event(e):
    if not isinstance(e,dict) or set(e)!=REQUIRED: raise ValueError("event fields do not match brief-event-v1")
    if e["schema_version"]!=SCHEMA_VERSION or e["frozen"] is not True: raise ValueError("event must be brief-event-v1 and frozen")
    if not EVENT_ID.fullmatch(e["event_id"]): raise ValueError("invalid event_id")
    captured=parse_dt(e["captured_at"]); published=parse_dt(e["published_at"],nullable=True)
    if captured>=PUBLICATION_REQUIRED_FROM and published is None: raise ValueError("published_at is required for new events")
    if published and published>captured: raise ValueError("published_at cannot be after captured_at")
    if captured>datetime.now(timezone.utc).astimezone(captured.tzinfo): raise ValueError("captured_at cannot be in the future")
    for f in ("title","factual_summary","theme","subtheme","sector"):
        if not isinstance(e[f],str) or not e[f].strip(): raise ValueError(f"{f} is required")
    for f,a in ENUMS.items():
        if e[f] not in a: raise ValueError(f"invalid {f}")
    for f in SCORES:
        v=e[f]
        if isinstance(v,bool) or not isinstance(v,int) or not 0<=v<=100: raise ValueError(f"{f} must be an integer from 0 to 100")
    for f in ("companies","tickers"):
        v=e[f]
        if not isinstance(v,list) or len(v)!=len(set(v)): raise ValueError(f"{f} must be a unique array")
    if any(not isinstance(t,str) or not TICKER.fullmatch(t) for t in e["tickers"]): raise ValueError("invalid ticker")
    if not isinstance(e["sources"],list) or not e["sources"]: raise ValueError("at least one source is required")
    for s in e["sources"]:
        if set(s)-{"url","source_name","source_type"} or not {"url","source_name"}<=set(s): raise ValueError("invalid source fields")
        p=urlparse(s["url"])
        if p.scheme not in {"http","https"} or not p.netloc or not s["source_name"].strip(): raise ValueError("source must have a valid HTTP(S) URL and name")
    st=e["story"]
    if not isinstance(st,dict) or set(st)!={"story_id","relation"} or st["relation"] not in RELATIONS: raise ValueError("invalid story")
    if st["relation"]!="NEW" and not st["story_id"]: raise ValueError("non-NEW story relation requires story_id")
    th=e["thesis"]
    if not isinstance(th,dict) or set(th)!={"thesis_ids","statement"}: raise ValueError("invalid thesis")
    if not isinstance(th["thesis_ids"],list) or len(th["thesis_ids"])!=len(set(th["thesis_ids"])): raise ValueError("thesis_ids must be a unique array")

def validate_journal(events):
    if not isinstance(events,list): raise ValueError("journal must be an array")
    seen=set(); previous=""
    for e in events:
        validate_event(e)
        if e["event_id"] in seen: raise ValueError("duplicate event_id")
        if e["captured_at"]<previous: raise ValueError("events must be ordered by captured_at")
        seen.add(e["event_id"]); previous=e["captured_at"]

def validate_append_only(previous,current):
    validate_journal(previous); validate_journal(current)
    if len(current)<len(previous) or current[:len(previous)]!=previous: raise ValueError("brief-event history is append-only; frozen events cannot change")

def main():
    paths=sorted(DATA_DIR.glob("????-??.json"))
    for path in paths:
        events=json.loads(path.read_text(encoding="utf-8")); validate_journal(events)
        for e in events:
            if e["captured_at"][:7]!=path.stem: raise ValueError(f"{e['event_id']} belongs in {e['captured_at'][:7]}.json")
    print(f"Validated {len(paths)} brief-event journal(s)")
if __name__=="__main__":
    try: main()
    except (ValueError,json.JSONDecodeError) as exc:
        print(f"brief-event validation failed: {exc}",file=sys.stderr); raise SystemExit(1)
