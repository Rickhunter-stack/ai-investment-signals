from datetime import date, datetime, timezone
from pathlib import Path
import json, math, os
import pandas as pd
import exchange_calendars as xcals
import yfinance as yf
from .db import connect

ROOT=Path(__file__).resolve().parents[1]
UNIVERSE=ROOT/"data/universe_seed.csv"; JOURNAL=ROOT/"data/market_pit"
CONFIRMATORY_SECURITIES=("NVDA","AVGO","QCOM","MU","GOOGL","AMZN","ADI","MDT","ISRG","GH")
BENCHMARK_TICKERS=("SPY","QQQ","SMH","IHI","XBI"); SOURCE="yahoo"
REQUEST={"period":"1mo","interval":"1d","auto_adjust":False,"repair":True,"actions":True}
REQUIRED_FIELDS=("ticker","session_date","raw_close","observed_at","source","collector","collector_version","request","series_type","frozen")

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
  if duplicate_dates: raise ValueError(f"duplicate vendor session dates for {ticker}: {sorted(duplicate_dates)}")
  max_date=max(dates) if dates else None
  # Yahoo Close is split-adjusted historically. Undo splits that occur AFTER each
  # session inside the same response, while retaining the vendor value for audit.
  splits=[]
  for idx,r in frame.iterrows():
   s=r.get("Stock Splits",0.0)
   if pd.notna(s) and float(s)>0: splits.append((idx.date(),float(s)))
  # Only split-labelled sessions are checked. Large genuine market moves
  # without a split are never censored. If Close shows the split ratio while
  # Adj Close remains continuous, the vendor Close convention is ambiguous.
  split_anomalies=[]
  valid=[]
  for idx,r in frame.iterrows():
   close=r.get("Close"); adj=r.get("Adj Close"); split=r.get("Stock Splits",0.0)
   if pd.notna(close) and math.isfinite(float(close)) and float(close)>0:
    valid.append((idx.date(),float(close),None if adj is None or pd.isna(adj) else float(adj),
                  0.0 if pd.isna(split) else float(split)))
  for (d0,p0,a0,_),(d1,p1,a1,s1) in zip(valid,valid[1:]):
   if s1>0 and a0 not in (None,0) and a1 not in (None,0):
    close_ratio=p0/p1; adj_ratio=a0/a1
    close_matches=abs(close_ratio/s1-1.0)<=0.15
    adj_continuous=abs(adj_ratio-1.0)<=0.15
    if close_matches and adj_continuous:
     split_anomalies.append({"session_date":d1.isoformat(),"kind":"split_close_not_adjusted",
                             "split_ratio":s1,"close_ratio":close_ratio,"adj_ratio":adj_ratio})
  for idx,r in frame.iterrows():
   d=idx.date()
   if max_date is None or not (max_date>d): continue
   close=r.get("Close")
   if pd.isna(close) or not math.isfinite(float(close)) or float(close)<=0: raise ValueError(f"invalid eligible Close for {ticker} {d}")
   factor=1.0
   for sd,s in splits:
    if sd>d: factor*=s
   vendor_close=float(close); raw_close=vendor_close*factor
   adj=r.get("Adj Close")
   vendor_div=r.get("Dividends",0.0)
   split=r.get("Stock Splits",0.0)
   vendor_div=float("nan") if pd.isna(vendor_div) else float(vendor_div)
   div=vendor_div*factor
   repaired=r.get("Repaired?",False)
   rows.append({"ticker":ticker,"session_date":d.isoformat(),"raw_close":raw_close,
    "vendor_close":vendor_close,"vendor_split_factor":factor,
    "vendor_adjusted_close":None if adj is None or pd.isna(adj) else float(adj),
    "dividend":div,"vendor_dividend":vendor_div,"split_ratio":float("nan") if pd.isna(split) else float(split),
    "repaired":False if pd.isna(repaired) else bool(repaired),"observed_at":observed_at,
    "source":SOURCE,"collector":"yfinance","collector_version":yf.__version__,
    "request":request,"series_type":series_type,"run_id":os.getenv("EXPERIMENT_RUN_ID"),"commit_sha":os.getenv("EXPERIMENT_COMMIT_SHA"),"quality_flags":list(split_anomalies),"frozen":True})
 return rows

def _latest_per_ticker(rows):
 newest={}
 for r in rows:
  old=newest.get(r["ticker"])
  if old is None or r["session_date"]>old["session_date"]: newest[r["ticker"]]=r
 return [newest[t] for t in sorted(newest)]

def _annotate_gap_metadata(newest,all_rows):
 existing=_load_journal()
 latest_existing={}
 for (ticker,session),_ in existing.items():
  if ticker not in latest_existing or session>latest_existing[ticker]: latest_existing[ticker]=session
 by_ticker={}
 for r in all_rows: by_ticker.setdefault(r["ticker"],[]).append(r)
 for r in newest:
  previous=latest_existing.get(r["ticker"])
  r["gap_sessions"]=[]
  r["gap_unbounded"]=False
  if not previous: continue
  r["gap_sessions"]=sorted(x["session_date"] for x in by_ticker.get(r["ticker"],[])
                           if previous < x["session_date"] < r["session_date"])
  if (date.fromisoformat(r["session_date"])-date.fromisoformat(previous)).days>31:
   r["gap_unbounded"]=True
 return newest

def _collection_boundary(raw,tickers):
 frames=_frames(raw,tickers); out={}
 for ticker,frame in frames.items():
  dates=sorted({idx.date() for idx in frame.dropna(how="all").index})
  if dates: out[ticker]=dates[-1].isoformat()
 return out

def _boundary_alignment(raw_groups):
 latest={}; calendar=set()
 for raw,tickers in raw_groups:
  for ticker,frame in _frames(raw,tickers).items():
   dates=sorted({idx.date() for idx in frame.dropna(how="all").index})
   calendar.update(dates)
   if dates: latest[ticker]=dates[-1]
 ordered=sorted(calendar); pos={d:i for i,d in enumerate(ordered)}
 if latest:
  span=max(pos[d] for d in latest.values())-min(pos[d] for d in latest.values())
  if span>1: raise RuntimeError(f"confirmatory vendor frontiers diverge by {span} sessions")
 else: span=0
 return {t:d.isoformat() for t,d in latest.items()},span

def _expected_xnys_frontier(observed_at):
 observed=pd.Timestamp(observed_at)
 if observed.tzinfo is None: observed=observed.tz_localize("UTC")
 else: observed=observed.tz_convert("UTC")
 cal=xcals.get_calendar("XNYS")
 sessions=cal.sessions_in_range((observed-pd.Timedelta(days=14)).date(),observed.date())
 opened=[s for s in sessions if cal.session_open(s)<=observed]
 if not opened: raise RuntimeError("cannot resolve XNYS frontier")
 return opened[-1].date().isoformat()

def _validate_calendar_frontier(boundary,observed_at):
 expected=_expected_xnys_frontier(observed_at)
 latest=max(boundary.values())
 if latest!=expected:
  raise RuntimeError(f"stale vendor frontier: latest={latest} expected_xnys={expected}")
 return expected

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

def _validate_confirmatory_rows(rows):
 expected=set(CONFIRMATORY_SECURITIES)|set(BENCHMARK_TICKERS)
 by_ticker={t:0 for t in expected}; seen=set()
 for r in rows:
  missing=[k for k in REQUIRED_FIELDS if k not in r]
  if missing: raise ValueError(f"market row missing fields: {missing}")
  if r["ticker"] not in expected: raise ValueError(f"unexpected confirmatory ticker: {r['ticker']}")
  key=(r["ticker"],r["session_date"])
  if key in seen: raise ValueError(f"duplicate collected market row: {key}")
  seen.add(key); by_ticker[r["ticker"]]+=1
  expected_type="security" if r["ticker"] in CONFIRMATORY_SECURITIES else "benchmark"
  if r["frozen"] is not True or r["series_type"]!=expected_type: raise ValueError(f"invalid integrity metadata: {key}")
  if not r.get("run_id") or not r.get("commit_sha"): raise ValueError(f"missing run provenance: {key}")
  if not math.isfinite(float(r["raw_close"])) or float(r["raw_close"])<=0: raise ValueError(f"invalid raw close: {key}")
  for field in ("dividend","split_ratio"):
   value=float(r.get(field,0.0))
   if not math.isfinite(value) or value<0: raise ValueError(f"invalid {field}: {key}")
  datetime.fromisoformat(r["observed_at"].replace("Z","+00:00"))
 missing=sorted(t for t,n in by_ticker.items() if n<1)
 if missing: raise RuntimeError(f"market collection incomplete; refusing confirmatory write; missing={missing}")
 return True

def _report_long_gaps(rows,lookback_days=31):
 existing=_load_journal()
 latest={}
 for (ticker,session),_ in existing.items():
  if ticker not in latest or session>latest[ticker]: latest[ticker]=session
 for r in rows:
  previous=latest.get(r["ticker"])
  if previous and (date.fromisoformat(r["session_date"])-date.fromisoformat(previous)).days>lookback_days:
   print(f"MARKET_GAP ticker={r['ticker']} previous={previous} resumed={r['session_date']} no_backfill=true")

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
 confirmatory_rows=_latest_per_ticker(rows)
 if confirmatory_writes_enabled():
  confirmatory_rows=_annotate_gap_metadata(confirmatory_rows,rows)
  try: _validate_confirmatory_rows(rows)
  except (ValueError,RuntimeError):
   conn.close(); raise
  boundary,alignment_span=_boundary_alignment(((raw,securities),(bench,list(BENCHMARK_TICKERS))))
  expected=set(securities)|set(BENCHMARK_TICKERS)
  if set(boundary)!=expected:
   conn.close(); raise RuntimeError(f"market boundary incomplete: {sorted(expected-set(boundary))}")
  global_boundary=_validate_calendar_frontier(boundary,observed_at)
  (ROOT/"data/market_boundary_runtime.json").write_text(json.dumps({"observed_at":observed_at,"latest_returned_session":boundary,"global_boundary":global_boundary,"alignment_span_sessions":alignment_span},sort_keys=True)+chr(10))
  _report_long_gaps(confirmatory_rows)
  fresh=_append_journal(confirmatory_rows)
 else:
  fresh=[]
 cache=[(r["ticker"],r["session_date"],r["raw_close"],None,r["observed_at"],r["source"],r["series_type"]) for r in fresh]
 conn.executemany("""INSERT OR IGNORE INTO market_pit (ticker,date,adjusted_close,volume,observed_at,source,series_type)
 VALUES(?,?,?,?,?,?,?)""",cache)
 legacy=[(r["ticker"],r["session_date"],r["raw_close"],None,None) for r in rows]
 conn.executemany("""INSERT INTO market(ticker,date,close,volume,market_cap) VALUES(?,?,?,?,?)
 ON CONFLICT(ticker,date) DO UPDATE SET close=excluded.close,volume=excluded.volume""",legacy)
 conn.commit(); conn.close(); return len(fresh)
