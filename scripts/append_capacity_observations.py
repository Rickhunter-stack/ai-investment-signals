"""Append Capacity Monitor observations (Session B only, after the weekly freeze).

The script sets observed_at (now, never backdated), the wall reference, ids and
versions. Drafts may not carry them. See docs/CAPACITY_MONITOR.md.
"""
from __future__ import annotations
import argparse, json, sys
from datetime import datetime, timezone
from pathlib import Path
import capacity_common as cc

def append(drafts,root=cc.ROOT,now=None,historical_seed=False):
    if not isinstance(drafts,list) or not drafts: raise ValueError("expected a non-empty JSON array of observation drafts")
    definitions,_=cc.load_definitions(root); refs=cc.weekly_refs(root)
    now=(now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    ref=cc.wall_ref(refs,now)
    existing=cc.load_observations(root)
    if existing and cc.ts(existing[-1]["observed_at"],"observed_at")>now: raise ValueError("journal already holds a later observation")
    day=now.strftime("%Y%m%d"); n=sum(o["observation_id"].startswith(f"CAP-{day}-") for o in existing)
    rows=[]
    for d in drafts:
        if not isinstance(d,dict): raise ValueError("each draft must be an object")
        forbidden=cc.SCRIPT_FIELDS&set(d)
        if forbidden: raise ValueError(f"drafts may not set {sorted(forbidden)}")
        cc.validate_draft(d,definitions); n+=1
        rows.append({"schema_version":cc.OBS_SCHEMA,"observation_id":f"CAP-{day}-{n:04d}","method_version":cc.METHOD,
                     **d,"observed_at":now.isoformat(),"weekly_snapshot_date":ref["date"],
                     "historical_seed":bool(historical_seed),"frozen":True})
    cc.validate_journal(existing+rows,definitions,refs)
    path=cc.paths(root)["observations"]/f"{now.strftime('%Y-%m')}.json"
    previous=json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    tmp=path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(previous+rows,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8"); tmp.replace(path)
    saved=json.loads(path.read_text(encoding="utf-8"))
    if saved[:len(previous)]!=previous or saved[len(previous):]!=rows: raise ValueError("post-write verification failed")
    return rows

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("drafts",type=Path,help="JSON array of observation drafts")
    p.add_argument("--historical-seed",action="store_true",help="bootstrap data collected before the module existed; observed_at stays the ingestion time")
    a=p.parse_args()
    rows=append(json.loads(a.drafts.read_text(encoding="utf-8")),historical_seed=a.historical_seed)
    print(f"Appended {len(rows)} capacity observation(s) behind weekly snapshot {rows[0]['weekly_snapshot_date']}")
if __name__=="__main__":
    try: main()
    except (ValueError,json.JSONDecodeError) as exc:
        print(f"capacity append failed: {exc}",file=sys.stderr); raise SystemExit(1)
