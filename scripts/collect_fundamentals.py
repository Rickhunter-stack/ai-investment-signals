from pathlib import Path
from datetime import datetime
import csv, json, math
import yfinance as yf

ROOT=Path(__file__).resolve().parents[1]
UNIVERSE=ROOT/'data'/'universe_seed.csv'
OUT=ROOT/'data'/'fundamentals.json'

def val(frame,names,col):
    for n in names:
        if n in frame.index:
            x=frame.loc[n,col]
            try:
                x=float(x)
                if math.isfinite(x): return x
            except Exception: pass
    return None

def pct(x): return None if x is None else round(100*x,2)
def cagr(a,b,n):
    if a is None or b is None or a<=0 or b<=0: return None
    return (b/a)**(1/n)-1

def one(ticker):
    t=yf.Ticker(ticker)
    cf=t.cashflow
    inc=t.financials
    bs=t.balance_sheet
    cols=sorted(set(cf.columns)&set(inc.columns)&set(bs.columns))
    rows=[]
    for col in cols:
        ocf=val(cf,['Operating Cash Flow','Total Cash From Operating Activities'],col)
        capex=val(cf,['Capital Expenditure','Capital Expenditures'],col)
        capex=abs(capex) if capex is not None else None
        revenue=val(inc,['Total Revenue','Operating Revenue'],col)
        opinc=val(inc,['Operating Income'],col)
        pretax=val(inc,['Pretax Income'],col)
        tax=val(inc,['Tax Provision','Income Tax Expense'],col)
        equity=val(bs,['Stockholders Equity','Total Stockholder Equity'],col)
        cash=val(bs,['Cash Cash Equivalents And Short Term Investments','Cash And Cash Equivalents'],col) or 0
        debt=val(bs,['Total Debt'],col) or 0
        shares=val(inc,['Diluted Average Shares','Basic Average Shares'],col)
        fcf=(ocf-capex) if ocf is not None and capex is not None else None
        tr=max(0,min(.35,tax/pretax)) if tax is not None and pretax and pretax>0 else .21
        nopat=opinc*(1-tr) if opinc is not None else None
        invested=(equity+debt-cash) if equity is not None else None
        roic=nopat/invested if nopat is not None and invested and invested>0 else None
        year=int(getattr(col,'year',str(col)[:4]))
        rows.append({'year':year,'revenue':revenue,'ocf':ocf,'capex':capex,'fcf':fcf,'capex_ocf_pct':pct(capex/ocf) if capex is not None and ocf and ocf>0 else None,'fcf_margin_pct':pct(fcf/revenue) if fcf is not None and revenue else None,'fcf_per_share':round(fcf/shares,4) if fcf is not None and shares and shares>0 else None,'roic_pct':pct(roic)})
    rows=sorted(rows,key=lambda x:x['year'])
    info=t.info or {}
    latest=rows[-1].copy() if rows else {}
    fcf=latest.get('fcf')
    mcap=info.get('marketCap')
    financial_currency=info.get('financialCurrency')
    market_currency=info.get('currency')
    same_currency=bool(financial_currency and market_currency and financial_currency==market_currency)
    latest['financial_currency']=financial_currency
    latest['market_currency']=market_currency
    latest['fcf_yield_currency_compatible']=same_currency
    latest['fcf_yield_pct']=pct(fcf/mcap) if fcf is not None and mcap and same_currency else None
    if len(rows)>=4:
        latest['fcf_cagr_available_pct']=pct(cagr(rows[0].get('fcf'),rows[-1].get('fcf'),rows[-1]['year']-rows[0]['year']))
        latest['fcf_per_share_cagr_available_pct']=pct(cagr(rows[0].get('fcf_per_share'),rows[-1].get('fcf_per_share'),rows[-1]['year']-rows[0]['year']))
    return {'ticker':ticker,'status':'ok' if rows else 'insufficient_data','latest':latest,'annual':rows}

def main():
    with UNIVERSE.open(encoding='utf-8') as f: tickers=[r['ticker'] for r in csv.DictReader(f)]
    data={'generated_at':datetime.utcnow().isoformat(timespec='seconds')+'Z','methodology':{'fcf':'OCF - capex','fcf_yield':'latest annual FCF / current market cap only when financial and market currencies match','roic':'NOPAT / (equity + debt - cash)','note':'V1 uses standardized Yahoo Finance statements. SEC/EDGAR 10-year history is the next source layer.'},'companies':{}}
    for ticker in tickers:
        try: data['companies'][ticker]=one(ticker)
        except Exception as e: data['companies'][ticker]={'ticker':ticker,'status':'error','error':str(e)[:160],'annual':[]}
    OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print(OUT)
if __name__=='__main__': main()
