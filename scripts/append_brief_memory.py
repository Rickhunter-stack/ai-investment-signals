"""Append one user-validated weekly brief to data/brief_memory.json.

Called by the session that wrote the brief, only after the user has explicitly
approved it. Never at generation time, never by hand. See docs/BRIEF_MEMORY.md.
"""
from __future__ import annotations
import argparse, json, sys
from datetime import datetime, timezone
from pathlib import Path
import validate_brief_memory as v
from check_append_only_git import assert_list_prefix

MEMORY=v.MEMORY

def append(entry,user_validated_at,now=None):
    if not isinstance(entry,dict): raise ValueError("expected one brief memory entry (JSON object)")
    if v.PROVENANCE_FIELDS&set(entry): raise ValueError("validation provenance is set by this script, not by the entry")
    now=(now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    validated=v._aware(user_validated_at,"--user-validated-at")
    if validated>now: raise ValueError("--user-validated-at is in the future")
    record={**entry,"validation":v.VALIDATION,"validated_at":validated.isoformat(),"archived_at":now.isoformat()}
    v.validate_entry(record)
    previous=json.loads(MEMORY.read_text(encoding="utf-8")) if MEMORY.exists() else []
    if any(e.get("date")==record["date"] for e in previous): raise ValueError(f"a brief dated {record['date']} is already archived")
    current=previous+[record]
    v.validate_history(current); assert_list_prefix(previous,current,str(MEMORY))
    tmp=MEMORY.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(current,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); tmp.replace(MEMORY)
    saved=json.loads(MEMORY.read_text(encoding="utf-8"))
    if saved[:len(previous)]!=previous or saved[-1]!=record: raise ValueError("post-write verification failed")
    return record

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("entry",type=Path,help="JSON file holding one brief entry")
    p.add_argument("--user-validated-at",required=True,help="ISO timestamp of the user's explicit approval of this brief")
    a=p.parse_args()
    record=append(json.loads(a.entry.read_text(encoding="utf-8")),a.user_validated_at)
    print(f"Archived brief {record['date']} (validated {record['validated_at']})")
if __name__=="__main__":
    try: main()
    except (ValueError,json.JSONDecodeError) as exc:
        print(f"brief memory append failed: {exc}",file=sys.stderr); raise SystemExit(1)
