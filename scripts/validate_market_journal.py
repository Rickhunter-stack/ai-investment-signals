#!/usr/bin/env python3
"""Validate the current immutable market journal schema and integrity."""
from __future__ import annotations
import json, math
from datetime import datetime, date
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; JOURNAL=ROOT/"data/market_pit"
SEC={"NVDA","AVGO","QCOM","MU","GOOGL","AMZN","ADI","MDT","ISRG","GH"}
BENCH={"SPY","QQQ","SMH","IHI","XBI"}; ALL=SEC|BENCH
REQUIRED={"ticker","session_date","raw_close","observed_at","source","collector","collector_version","request","series_type","run_id","commit_sha","gap_sessions","gap_unbounded","quality_flags","frozen"}

def validate():
 seen=set(); count=0
 if not JOURNAL.exists(): return 0
 for p in sorted(JOURNAL.glob("*.json")):
  rows=json.loads(p.read_text())
  if not isinstance(rows,list): raise ValueError(f"{p}: expected JSON array")
  for r in rows:
   missing=REQUIRED-set(r)
   if missing: raise ValueError(f"{p}: missing {sorted(missing)}")
   key=(r["ticker"],r["session_date"])
   if key in seen: raise ValueError(f"duplicate {key}")
   seen.add(key); count+=1
   if r["ticker"] not in ALL: raise ValueError(f"unexpected ticker {key}")
   if r["frozen"] is not True: raise ValueError(f"not frozen {key}")
   if r["series_type"] != ("security" if r["ticker"] in SEC else "benchmark"): raise ValueError(f"wrong series type {key}")
   date.fromisoformat(r["session_date"]); datetime.fromisoformat(r["observed_at"].replace("Z","+00:00"))
   if not math.isfinite(float(r["raw_close"])) or float(r["raw_close"])<=0: raise ValueError(f"bad raw_close {key}")
   for f in ("dividend","split_ratio"):
    v=float(r.get(f,0));
    if not math.isfinite(v) or v<0: raise ValueError(f"bad {f} {key}")
   if not r["collector_version"] or not isinstance(r["request"],dict) or not r["run_id"] or not r["commit_sha"]: raise ValueError(f"missing provenance {key}")
   if not isinstance(r["gap_sessions"],list) or not isinstance(r["gap_unbounded"],bool) or not isinstance(r["quality_flags"],list): raise ValueError(f"invalid quality metadata {key}")
 return count
if __name__=="__main__":
 print(f"market journal validated: {validate()} row(s)")
