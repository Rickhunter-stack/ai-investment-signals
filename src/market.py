from datetime import datetime, timezone
from pathlib import Path
import json, os
import pandas as pd
import yfinance as yf
from .db import connect

ROOT=Path(__file__).resolve().parents[1]
UNIVERSE=ROOT/"data/universe_seed.csv"; JOURNAL=ROOT/"data/market_pit"
CONFIRMATORY_SECURITIES=("NVDA","AVGO","QCOM","MU","GOOGL","AMZN","ADI","MDT","ISRG","GH")
BENCHMARK_TICKERS=("SPY","QQQ","SMH","IHI","XBI"); SOURCE="yahoo"
REQUEST={"period":"1mo","interval":"1d","auto_adjust":False,"repair":True,"actions":True}

def seed_companies(conn):
 df=pd.read_csv(UNIVERSE)
 conn.executemany("""INSERT INTO companies(ticker,company,theme,role,subtheme,priority) VALUES(?,?,?,?,?,?)
 ON CONFLICT(ticker) DO UPDATE SET company=excluded.company,theme=excluded.theme,role=excluded.role,
 subtheme=excluded.subtheme,priority=excluded.priority""",df[["ticker","company","theme","role","subtheme","priority"]].itertuples(index=False,name=None))
 conn.commit(); return df

def _frames(raw,tickers):
 if isinstance(raw.columns,pd.MultiIndex):
  level0=set(raw.columns.get_level_values(0))
  if set(tickers)&level0: return {t:raw[t] for t in tickers if t in level0}
  level1=set(raw.columns.get_level_values(1))
  if set(tickers)&level1: return {t:raw.xs(t,axis=1,level=1) for t in tickers if t in level1}
 return {tickers[0]:raw} if len(tickers)==1 else {}

def _eligible_rows(raw,tickers,observed_at,series_type,request=None):
 rows=[]; request=dict(request or REQUEST)
 for ticker,frame in _frames(raw,tickers).items():
  frame=frame.dropna(how="all").sort_index()
  dates=[idx.date() for idx in frame.index]
  duplicate_dates={d for d in dates if dates.count(d)>1}
  max_date=max(dates) if dates else None
  # Yahoo Close is split-adjusted historically. Undo splits that occur AFTER each
  # session inside the same response, while retaining the vendor value for audit.
  splits=[]
  for idx,r in frame.iterrows():
   s=r.get("Stock Splits",0.0)
   if pd.notna(s) and float(s)>0: splits.append((idx.date(),float(s)))
  for idx,r in frame.iterrows():
   d=idx.date()
   if d in duplicate_dates or max_date is None or not (max_date>d): continue
   close=r.get("Close")
   if pd.isna(close) or float(close)<=0: continue
   factor=1.0
   for sd,s in splits:
    if sd>d: factor*=s
   vendor_close=float(close); raw_close=vendor_close*factor
   adj=r.get("Adj Close"); vendor_div=r.get("Dividends",0.0); split=r.get("Stock Splits",0.0)\n   vendor_div=0.0 if pd.isna(vendor_div) else float(vendor_div); div=vendor_div*factor
   repaired=r.get("Repaired?",False)
   rows.append({"ticker":ticker,"session_date":d.isoformat(),"raw_close":raw_close,
    "vendor_close":vendor_close,"vendor_split_factor":factor,
    "vendor_adjusted_close":None if adj is None or pd.isna(adj) else float(adj),
    "dividend":div,"vendor_dividend":vendor_div,"split_ratio":0.0 if pd.isna(split) else float(split),
    "repaired":False if pd.isna(repaired) else bool(repaired),"observed_at":observed_at,
    "source":SOURCE,"collector":"yfinance","collector_version":yf.__version__,
    "request":request,"series_type":series_type,"frozen":True})
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
 JOURNAL.mkdir(parents=True,exist_ok=True); existing=_load_journal(); fresh=[]
 for r in sorted(rows,key=lambda x:(x["session_date"],x["ticker"])):
  key=(r["ticker"],r["session_date"])
  if key not in existing: existing[key]=r; fresh.append(r)
 by_month={}
 for r in fresh: by_month.setdefault(r["session_date"][:7],[]).append(r)
 for month,items in by_month.items():
  path=JOURNAL/f"{month}.json"; old=json.loads(path.read_text()) if path.exists() else []
  tmp=path.with_suffix(".json.tmp")
  tmp.write_text(json.dumps(old+items,indent=2,ensure_ascii=False,allow_nan=False)+"\n"); os.replace(tmp,path)
 return fresh

def confirmatory_writes_enabled(): return os.getenv("CONFIRMATORY_WRITE")=="1"

def update_market(period="1mo"):
 conn=connect(); seed_companies(conn); securities=list(CONFIRMATORY_SECURITIES)
 observed_at=datetime.now(timezone.utc).isoformat(); kwargs=dict(REQUEST); kwargs["period"]=period
 raw=yf.download(tickers=securities,group_by="ticker",progress=False,threads=True,**kwargs)
 bench=yf.download(tickers=list(BENCHMARK_TICKERS),group_by="ticker",progress=False,threads=True,**kwargs)
 rows=_eligible_rows(raw,securities,observed_at,"security",kwargs)+_eligible_rows(bench,list(BENCHMARK_TICKERS),observed_at,"benchmark",kwargs)
 expected=set(securities)|set(BENCHMARK_TICKERS); present={r["ticker"] for r in rows}; missing=sorted(expected-present)
 if not rows or missing:
  conn.close(); raise RuntimeError(f"market collection incomplete; refusing confirmatory write; missing={missing}")
 fresh=_append_journal(rows) if confirmatory_writes_enabled() else []
 cache=[(r["ticker"],r["session_date"],r["raw_close"],None,r["observed_at"],r["source"],r["series_type"]) for r in fresh]
 conn.executemany("""INSERT OR IGNORE INTO market_pit (ticker,date,adjusted_close,volume,observed_at,source,series_type)
 VALUES(?,?,?,?,?,?,?)""",cache)
 legacy=[(r["ticker"],r["session_date"],r["raw_close"],None,None) for r in rows]
 conn.executemany("""INSERT INTO market(ticker,date,close,volume,market_cap) VALUES(?,?,?,?,?)
 ON CONFLICT(ticker,date) DO UPDATE SET close=excluded.close,volume=excluded.volume""",legacy)
 conn.commit(); conn.close(); return len(fresh)
