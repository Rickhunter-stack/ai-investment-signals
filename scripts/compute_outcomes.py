#!/usr/bin/env python3
"""Deterministic prospective outcome engine for preregistered weekly-v1 observations."""
from __future__ import annotations
import calendar, hashlib, json, os, sqlite3
from datetime import datetime, date, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/"data/veille.db"
WEEKLY=ROOT/"data/weekly_signals.json"
OUT=ROOT/"data/outcomes_v1.json"
PROTOCOL=ROOT/"PREREGISTRATION.md"
UNIVERSE={"NVDA":"QQQ","AVGO":"QQQ","QCOM":"QQQ","MU":"QQQ","GOOGL":"QQQ","AMZN":"QQQ","ADI":"QQQ",
          "MDT":"SPY","ISRG":"SPY","GH":"SPY"}
HORIZONS={"M1":1,"M3":3,"M6":6,"M12":12}
PROTOCOL_START=datetime.fromisoformat("2026-09-17T00:00:00+00:00")
SCHEMA="outcome-v1"

def protocol_sha256():
    return hashlib.sha256(PROTOCOL.read_bytes()).hexdigest()

def add_months(d: date, months: int)->date:
    m=d.month-1+months; y=d.year+m//12; m=m%12+1
    return date(y,m,min(d.day,calendar.monthrange(y,m)[1]))

def load_market(conn):
    rows=conn.execute("SELECT ticker,date,adjusted_close,observed_at FROM market_pit ORDER BY date").fetchall()
    out={}
    for t,d,p,obs in rows: out.setdefault(t,[]).append((date.fromisoformat(d),float(p),obs))
    return out

def common_price(market,ticker,bench,on_or_after):
    a={d:(p,o) for d,p,o in market.get(ticker,[]) if d>=on_or_after}
    b={d:(p,o) for d,p,o in market.get(bench,[]) if d>=on_or_after}
    common=sorted(set(a)&set(b))
    if not common:return None
    d=common[0]; return d,a[d][0],b[d][0],a[d][1],b[d][1]

def append_unique(existing,rows):
    ids={r["outcome_id"] for r in existing}
    return existing+[r for r in rows if r["outcome_id"] not in ids]

def build_rows(snapshots,market,now,existing=None):
    rows=[]; existing=existing or []
    anchors={r["outcome_id"]:r for r in existing if r.get("status")=="anchored"}
    now=now.astimezone(timezone.utc)
    phash=protocol_sha256()
    run_id=os.getenv("EXPERIMENT_RUN_ID"); commit_sha=os.getenv("EXPERIMENT_COMMIT_SHA")
    for snap in snapshots:
        captured=datetime.fromisoformat(snap["captured_at"].replace("Z","+00:00")).astimezone(timezone.utc)
        if captured<PROTOCOL_START or not snap.get("frozen"): continue
        start=captured.date() if captured.hour>=20 else date.fromordinal(captured.date().toordinal()+1)
        for ticker,score in snap.get("scores",{}).items():
            if ticker not in UNIVERSE: continue
            bench=UNIVERSE[ticker]; base=f'{snap["date"]}:{ticker}:{snap["method_version"]}'; t0_id=f"{base}:T0"
            anchor=anchors.get(t0_id)
            if anchor:
                if not anchor.get("eligible_confirmatory",False): continue
                t0d=date.fromisoformat(anchor["t0_date"]); p0=anchor["security_t0"]; b0=anchor["benchmark_t0"]
            else:
                t0=common_price(market,ticker,bench,start)
                if not t0: continue
                t0d,p0,b0,sobs,bobs=t0
                anchor={"schema_version":SCHEMA,"outcome_id":t0_id,"snapshot_date":snap["date"],
                    "ticker":ticker,"benchmark":bench,"method_version":snap["method_version"],
                    "signal_score":score.get("signal_score"),"t0_date":t0d.isoformat(),
                    "security_t0":p0,"benchmark_t0":b0,"security_observed_at":sobs,"benchmark_observed_at":bobs,
                    "eligible_confirmatory":True,"eligibility_decided_at":now.isoformat(),
                    "protocol_sha256":phash,"run_id":run_id,"commit_sha":commit_sha,"status":"anchored","frozen":True}
                rows.append(anchor)
            for label,months in HORIZONS.items():
                target=add_months(t0d,months)
                if now.date()<target: continue
                hp=common_price(market,ticker,bench,target)
                if not hp: continue
                hd,ph,bh,sobs,bobs=hp; sr=ph/p0-1; br=bh/b0-1
                rows.append({"schema_version":SCHEMA,"outcome_id":f"{base}:{label}","snapshot_date":snap["date"],
                    "ticker":ticker,"benchmark":bench,"method_version":snap["method_version"],
                    "signal_score":score.get("signal_score"),"horizon":label,"target_date":target.isoformat(),
                    "measurement_date":hd.isoformat(),"t0_date":t0d.isoformat(),
                    "security_return":round(sr,10),"benchmark_return":round(br,10),"excess_return":round(sr-br,10),
                    "eligible_confirmatory":True,"protocol_sha256":anchor.get("protocol_sha256",phash),
                    "t0_security_observed_at":anchor.get("security_observed_at"),
                    "t0_benchmark_observed_at":anchor.get("benchmark_observed_at"),
                    "measurement_security_observed_at":sobs,"measurement_benchmark_observed_at":bobs,
                    "run_id":run_id,"commit_sha":commit_sha,"status":"measured","frozen":True})
    return rows

def main():
    snaps=json.loads(WEEKLY.read_text())
    conn=sqlite3.connect(DB); market=load_market(conn); conn.close()
    existing=json.loads(OUT.read_text()) if OUT.exists() else []
    rows=build_rows(snaps,market,datetime.now(timezone.utc),existing)
    updated=append_unique(existing,rows)
    OUT.write_text(json.dumps(updated,indent=2,ensure_ascii=False,allow_nan=False)+"\n")
    print(f"outcomes: appended {len(updated)-len(existing)} immutable row(s)")

if __name__=="__main__": main()
