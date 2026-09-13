from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import yfinance as yf
from .db import connect

UNIVERSE = Path('data/universe_seed.csv')
BENCHMARK_TICKER = 'URTH'


def seed_companies(conn):
    df = pd.read_csv(UNIVERSE)
    conn.executemany(
        '''INSERT INTO companies(ticker, company, theme, role, subtheme, priority)
           VALUES(?,?,?,?,?,?)
           ON CONFLICT(ticker) DO UPDATE SET
             company=excluded.company,
             theme=excluded.theme,
             role=excluded.role,
             subtheme=excluded.subtheme,
             priority=excluded.priority''',
        df[['ticker','company','theme','role','subtheme','priority']].itertuples(index=False, name=None)
    )
    conn.commit()
    return df


def update_market(period='5d'):
    conn = connect()
    df = seed_companies(conn)
    tickers = df['ticker'].tolist()
    raw = yf.download(tickers=tickers, period=period, interval='1d', group_by='ticker', auto_adjust=False, progress=False, threads=True)
    rows = []
    if len(tickers) == 1:
        ticker = tickers[0]
        for idx, r in raw.iterrows():
            rows.append((ticker, idx.date().isoformat(), float(r.get('Close')) if pd.notna(r.get('Close')) else None, float(r.get('Volume')) if pd.notna(r.get('Volume')) else None, None))
    else:
        for ticker in tickers:
            if ticker not in raw.columns.get_level_values(0):
                continue
            frame = raw[ticker].dropna(how='all')
            for idx, r in frame.iterrows():
                close = r.get('Close')
                volume = r.get('Volume')
                rows.append((ticker, idx.date().isoformat(), float(close) if pd.notna(close) else None, float(volume) if pd.notna(volume) else None, None))

    # Benchmark kept outside the investable universe. auto_adjust=True makes the
    # series suitable as a total-return proxy by incorporating distributions.
    bench = yf.download(BENCHMARK_TICKER, period=period, interval='1d', auto_adjust=True, repair=True, progress=False)
    if not bench.empty:
        close = bench['Close']
        volume = bench['Volume'] if 'Volume' in bench else None
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        if isinstance(volume, pd.DataFrame):
            volume = volume.iloc[:, 0]
        for idx, value in close.dropna().items():
            vol = None if volume is None else volume.get(idx)
            rows.append((BENCHMARK_TICKER, idx.date().isoformat(), float(value), float(vol) if vol is not None and pd.notna(vol) else None, None))

    conn.executemany(
        '''INSERT INTO market(ticker,date,close,volume,market_cap)
           VALUES(?,?,?,?,?)
           ON CONFLICT(ticker,date) DO UPDATE SET close=excluded.close, volume=excluded.volume''', rows
    )
    conn.commit()
    conn.close()
    return len(rows)
