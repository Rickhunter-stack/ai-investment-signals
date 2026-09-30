"""Freeze one Capacity Monitor snapshot per weekly Signal period (after the wall).

Writes only when CAPACITY_WRITE=1 (the scheduled capacity-monitor workflow).
"""
from __future__ import annotations
import json, os, sys
from datetime import datetime, timezone
import capacity_common as cc

def build(root=cc.ROOT,now=None):
    definitions,sha=cc.load_definitions(root); refs=cc.weekly_refs(root); observations=cc.load_observations(root)
    cc.validate_journal(observations,definitions,refs)
    now=(now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    ref=cc.wall_ref(refs,now)
    snapshots=cc.load_snapshots(root)
    if any(s["weekly_snapshot_date"]==ref["date"] and s["method_version"]==cc.METHOD for s in snapshots): return None
    return cc.compute(definitions,sha,observations,now,ref)

def write(snapshot,root=cc.ROOT):
    path=cc.paths(root)["snapshots"]; previous=cc.load_snapshots(root); current=previous+[snapshot]
    definitions,sha=cc.load_definitions(root)
    cc.validate_snapshots(current,definitions,sha,cc.load_observations(root),cc.weekly_refs(root))
    tmp=path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(current,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8"); tmp.replace(path)
    if json.loads(path.read_text(encoding="utf-8"))[:len(previous)]!=previous: raise ValueError("post-write verification failed")

def main():
    snapshot=build()
    if snapshot is None: print("capacity: snapshot already frozen for the current weekly period"); return
    if os.getenv("CAPACITY_WRITE")!="1":
        print(f"capacity: dry-run; would freeze {snapshot['snapshot_id']} ({snapshot['counts']['observations']} observation(s))"); return
    write(snapshot); print(f"capacity: froze {snapshot['snapshot_id']}")
if __name__=="__main__":
    try: main()
    except (ValueError,json.JSONDecodeError) as exc:
        print(f"capacity snapshot failed: {exc}",file=sys.stderr); raise SystemExit(1)
