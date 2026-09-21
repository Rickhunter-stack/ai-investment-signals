#!/usr/bin/env python3
"""Deterministic prospective outcomes from the immutable Git market journal."""
from __future__ import annotations
import calendar, hashlib, json, os
from datetime import datetime,date,timezone
from zoneinfo import ZoneInfo
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; MARKET=ROOT/"data/market_pit"
WEEKLY=ROOT/"data/weekly_signals.json"; OUT=ROOT/"data/outcomes_v1.json"; PROTOCOL=ROOT/"PREREGISTRATION.md"
UNIVERSE={"NVDA":"QQQ","AVGO":"QQQ","QCOM":"QQQ","MU":"QQQ","GOOGL":"QQQ","AMZN":"QQQ","ADI":"QQQ","MDT":"SPY","ISRG":"SPY","GH":"SPY"}
HORIZONS={"M1":1,"M3":3,"M6":6,"M12":12}; PROTOCOL_START=datetime.fromisoformat("2026-09-17T00:00:00+00:00"); SCHEMA="outcome-v1.1"

def protocol_sha256(): return hashlib.sha256(PROTOCOL.read_bytes()).hexdigest()
def add_months(d,months):
 m=d.month-1+months; y=d.year+m//12; m=m%12+1
 return date(y,m,min(d.day,calendar.monthrange(y,m)[1]))

def load_market(path=MARKET):
 out={}
 if not path.exists(): return out
 for p in sorted(path.glob("*.json")):
  rows=json.loads(p.read_text())
  if not isinstance(rows,list): raise ValueError(f"{p}: expected array")
  for r in rows:
   if r.get("frozen") is not True or not r.get("observed_at") or float(r["raw_close"])<=0: raise ValueError(f"{p}: malformed frozen row")
   key=(r["ticker"],r["session_date"])
   if key in out: raise ValueError(f"duplicate market row {key}")
   out.setdefault(r["ticker"],[]).append(r)
 for rows in out.values(): rows.sort(key=lambda r:r["session_date"])
 return out

def common_row(market,ticker,bench,on_or_after,observed_after=None,observed_before=None):
 def eligible(r):
  return date.fromisoformat(r["session_date"])>=on_or_after and (observed_after is None or datetime.fromisoformat(r["observed_at"])>=observed_after) and (observed_before is None or datetime.fromisoformat(r["observed_at"])<=observed_before)
 a={date.fromisoformat(r["session_date"]):r for r in market.get(ticker,[]) if eligible(r)}
 b={date.fromisoformat(r["session_date"]):r for r in market.get(bench,[]) if eligible(r)}
 common=sorted(set(a)&set(b))
 return None if not common else (common[0],a[common[0]],b[common[0]])

def t0_row(market,ticker,bench,captured):
 ny=captured.astimezone(ZoneInfo("America/New_York"))
 # A session already frozen by snapshot time is admissible; otherwise a post-close
 # snapshot must wait for a strictly later session. Early-close handling is a v1.2 item.
 prior=common_row(market,ticker,bench,ny.date(),observed_before=captured)
 if prior: return prior
 start=date.fromordinal(ny.date().toordinal()+1) if ny.hour>=16 else ny.date()
 return common_row(market,ticker,bench,start,observed_after=captured)

def total_return(rows,t0,h):
 base=next(r for r in rows if r["session_date"]==t0.isoformat()); parts=1.0
 for r in rows:
  d=date.fromisoformat(r["session_date"])
  if not t0<d<=h: continue
  s=float(r.get("split_ratio") or 0)
  if s>0: parts*=s
  div=float(r.get("dividend") or 0)
  if div: parts+=parts*div/float(r["raw_close"])
 end=next(r for r in rows if r["session_date"]==h.isoformat())
 return parts*float(end["raw_close"])/float(base["raw_close"])-1

def append_unique(existing,rows):
 ids={r["outcome_id"] for r in existing}; return existing+[r for r in rows if r["outcome_id"] not in ids]

def build_rows(snapshots,market,now,existing=None):
 rows=[]; existing=existing or []; anchors={r["outcome_id"]:r for r in existing if r.get("status")=="anchored"}
 now=now.astimezone(timezone.utc); phash=protocol_sha256(); run=os.getenv("EXPERIMENT_RUN_ID"); sha=os.getenv("EXPERIMENT_COMMIT_SHA")
 for snap in snapshots:
  captured=datetime.fromisoformat(snap["captured_at"].replace("Z","+00:00")).astimezone(timezone.utc)
  if captured<PROTOCOL_START or not snap.get("frozen"): continue
  for ticker,score in snap.get("scores",{}).items():
   if ticker not in UNIVERSE: continue
   bench=UNIVERSE[ticker]; base=f'{snap["date"]}:{ticker}:{snap["method_version"]}'; oid=f"{base}:T0"; anchor=anchors.get(oid)
   if anchor:
    if not anchor.get("eligible_confirmatory",False): continue
    t0d=date.fromisoformat(anchor["t0_date"])
   else:
    hit=t0_row(market,ticker,bench,captured)
    if not hit: continue
    t0d,s,b=hit
    anchor={"schema_version":SCHEMA,"outcome_id":oid,"snapshot_date":snap["date"],"ticker":ticker,"benchmark":bench,
      "method_version":snap["method_version"],"signal_score":score.get("signal_score"),"t0_date":t0d.isoformat(),
      "security_t0":s["raw_close"],"benchmark_t0":b["raw_close"],"security_observed_at":s["observed_at"],"benchmark_observed_at":b["observed_at"],"eligible_confirmatory":True,
      "eligibility_decided_at":now.isoformat(),"protocol_sha256":phash,"run_id":run,"commit_sha":sha,"status":"anchored","frozen":True}
    rows.append(anchor)
   for label,months in HORIZONS.items():
    target=add_months(t0d,months)
    if now.date()<target: continue
    hit=common_row(market,ticker,bench,target)
    if not hit: continue
    hd,_,_=hit
    sr=total_return(market[ticker],t0d,hd); br=total_return(market[bench],t0d,hd)
    rows.append({"schema_version":SCHEMA,"outcome_id":f"{base}:{label}","snapshot_date":snap["date"],"ticker":ticker,
      "benchmark":bench,"method_version":snap["method_version"],"signal_score":score.get("signal_score"),"horizon":label,
      "target_date":target.isoformat(),"measurement_date":hd.isoformat(),"t0_date":t0d.isoformat(),
      "security_return":round(sr,10),"benchmark_return":round(br,10),"excess_return":round(sr-br,10),
      "eligible_confirmatory":True,"protocol_sha256":anchor.get("protocol_sha256",phash),"t0_security_observed_at":anchor.get("security_observed_at"),"t0_benchmark_observed_at":anchor.get("benchmark_observed_at"),"measurement_security_observed_at":hit[1]["observed_at"],"measurement_benchmark_observed_at":hit[2]["observed_at"],"run_id":run,"commit_sha":sha,
      "status":"measured","frozen":True})
 return rows

def main():
 if os.getenv("CONFIRMATORY_WRITE")!="1":
  print("outcomes: dry-run; confirmatory writes disabled"); return
 snaps=json.loads(WEEKLY.read_text()); market=load_market(); existing=json.loads(OUT.read_text()) if OUT.exists() else []
 updated=append_unique(existing,build_rows(snaps,market,datetime.now(timezone.utc),existing))
 OUT.write_text(json.dumps(updated,indent=2,ensure_ascii=False,allow_nan=False)+chr(10))
 print(f"outcomes: appended {len(updated)-len(existing)} immutable row(s)")
if __name__=="__main__": main()
