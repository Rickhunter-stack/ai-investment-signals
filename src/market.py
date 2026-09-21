from datetime import datetime, timezone
from pathlib import Path
import json
import os
import pandas as pd
import yfinance as yf
from .db import connect

UNIVERSE=Path("data/universe_seed.csv")
JOURNAL=Path("data/market_pit")
BENCHMARK_TICKERS=("SPY","QQQ","SMH","IHI","XBI")
SOURCE="yfinance"
REQUEST={"period":"1mo","interval":"1d","auto_adjust":False,"repair":True,"actions":True}

def seed_companies(conn):
    df=pd.read_csv(UNIVERSE)
    conn.executemany("""INSERT INTO companies(ticker,company,theme,role,subtheme,priority)
    VALUES(?,?,?,?,?,?) ON CONFLICT(ticker) DO UPDATE SET company=excluded.company,theme=excluded.theme,
    role=excluded.role,subtheme=excluded.subtheme,priority=excluded.priority""",
    df[["ticker","company","theme","role","subtheme","priority"]].itertuples(index=False,name=None))
    conn.commit(); return df

def _frames(raw,tickers):
    if len(tickers)==1: return {tickers[0]:raw}
    if not isinstance(raw.columns,pd.MultiIndex): return {}
    available=set(raw.columns.get_level_values(0))
    return {t:raw[t] for t in tickers if t in available}

def _eligible_rows(raw,tickers,observed_at,series_type):
    rows=[]
    for ticker,frame in _frames(raw,tickers).items():
        frame=frame.dropna(how="all").sort_index()
        # A bar is eligible only if the same vendor response contains a later daily bar.
        for i,(idx,r) in enumerate(frame.iterrows()):
            if i==len(frame)-1: continue
            close=r.get("Close")
            if pd.isna(close) or float(close)<=0: continue
            adj=r.get("Adj Close",close); div=r.get("Dividends",0.0); split=r.get("Stock Splits",0.0)
            rows.append({"ticker":ticker,"session_date":idx.date().isoformat(),"raw_close":float(close),
                "vendor_adjusted_close":None if pd.isna(adj) else float(adj),
                "dividend":0.0 if pd.isna(div) else float(div),"split_ratio":0.0 if pd.isna(split) else float(split),
                "observed_at":observed_at,"source":SOURCE,"collector":"yfinance",
                "request":REQUEST,"series_type":series_type,"frozen":True})
    return rows

def _load_journal():
    out={}
    if JOURNAL.exists():
        for p in sorted(JOURNAL.glob("*.json")):
            data=json.loads(p.read_text())
            if not isinstance(data,list): raise ValueError(f"{p}: market journal must be an array")
            for r in data:
                key=(r["ticker"],r["session_date"])
                if key in out: raise ValueError(f"duplicate market observation: {key}")
                out[key]=r
    return out

def _append_journal(rows):
    JOURNAL.mkdir(parents=True,exist_ok=True)
    existing=_load_journal(); fresh=[]
    for r in sorted(rows,key=lambda x:(x["session_date"],x["ticker"])):
        key=(r["ticker"],r["session_date"])
        if key not in existing: existing[key]=r; fresh.append(r)
    by_month={}
    for r in fresh: by_month.setdefault(r["session_date"][:7],[]).append(r)
    for month,items in by_month.items():
        path=JOURNAL/f"{month}.json"
        old=json.loads(path.read_text()) if path.exists() else []
        path.write_text(json.dumps(old+items,indent=2,ensure_ascii=False,allow_nan=False)+"\n")
    return fresh

def update_market(period="1mo"):
    conn=connect(); df=seed_companies(conn); securities=df["ticker"].tolist()
    observed_at=datetime.now(timezone.utc).isoformat()
    kwargs=dict(REQUEST); kwargs["period"]=period
    raw=yf.download(tickers=securities,group_by="ticker",progress=False,threads=True,**kwargs)
    bench=yf.download(tickers=list(BENCHMARK_TICKERS),group_by="ticker",progress=False,threads=True,**kwargs)
    rows=_eligible_rows(raw,securities,observed_at,"security")+_eligible_rows(bench,list(BENCHMARK_TICKERS),observed_at,"benchmark")
    expected=set(securities)|set(BENCHMARK_TICKERS); present={r["ticker"] for r in rows}
    missing=sorted(expected-present)
    if not rows or missing:
        conn.close(); raise RuntimeError(f"market collection incomplete; refusing confirmatory write; missing={missing}")
    confirmatory=os.getenv("CONFIRMATORY_WRITE")=="1"
    fresh=_append_journal(rows) if confirmatory else []
    # SQLite is cache/dashboard only. Rebuild compatible rows from newly frozen raw closes.
    cache=[(r["ticker"],r["session_date"],r["raw_close"],None,r["observed_at"],r["source"],r["series_type"]) for r in fresh]
    conn.executemany("""INSERT OR IGNORE INTO market_pit
      (ticker,date,adjusted_close,volume,observed_at,source,series_type) VALUES(?,?,?,?,?,?,?)""",cache)
    legacy=[(r["ticker"],r["session_date"],r["raw_close"],None,None) for r in rows]
    conn.executemany("""INSERT INTO market(ticker,date,close,volume,market_cap) VALUES(?,?,?,?,?)
      ON CONFLICT(ticker,date) DO UPDATE SET close=excluded.close,volume=excluded.volume""",legacy)
    conn.commit(); conn.close(); return len(fresh)
