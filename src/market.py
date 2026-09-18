from datetime import datetime, timezone, time
from zoneinfo import ZoneInfo
from pathlib import Path
import pandas as pd
import yfinance as yf
from .db import connect

UNIVERSE = Path('data/universe_seed.csv')
BENCHMARK_TICKERS = ('SPY', 'QQQ')
SOURCE = 'yfinance'


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


def _last_complete_session_date(now_utc):
    """Conservative US-equity daily-bar cutoff: today is eligible only after 16:15 ET."""
    ny = now_utc.astimezone(ZoneInfo('America/New_York'))
    if ny.time() >= time(16, 15):
        return ny.date()
    return date_from_ordinal(ny.date().toordinal() - 1)


def date_from_ordinal(value):
    from datetime import date
    return date.fromordinal(value)


def _rows(raw, tickers, observed_at, series_type, max_session_date=None):
    rows = []
    if len(tickers) == 1:
        frames = {tickers[0]: raw}
    else:
        available = set(raw.columns.get_level_values(0)) if isinstance(raw.columns, pd.MultiIndex) else set()
        frames = {ticker: raw[ticker] for ticker in tickers if ticker in available}
    for ticker, frame in frames.items():
        frame = frame.dropna(how='all')
        for idx, r in frame.iterrows():
            if max_session_date is not None and idx.date() > max_session_date:
                continue
            close, volume = r.get('Close'), r.get('Volume')
            if pd.isna(close):
                continue
            rows.append((ticker, idx.date().isoformat(), float(close),
                         float(volume) if pd.notna(volume) else None,
                         observed_at, SOURCE, series_type))
    return rows


def update_market(period='5d'):
    conn = connect()
    df = seed_companies(conn)
    tickers = df['ticker'].tolist()
    now_utc = datetime.now(timezone.utc)
    observed_at = now_utc.isoformat()
    max_session_date = _last_complete_session_date(now_utc)

    # One convention for every performance series: adjusted close. This avoids
    # comparing raw security prices with an adjusted benchmark series.
    raw = yf.download(tickers=tickers, period=period, interval='1d', group_by='ticker',
                      auto_adjust=True, repair=True, progress=False, threads=True)
    security_rows = _rows(raw, tickers, observed_at, 'security', max_session_date)

    bench_raw = yf.download(tickers=list(BENCHMARK_TICKERS), period=period, interval='1d',
                            group_by='ticker', auto_adjust=True, repair=True,
                            progress=False, threads=True)
    benchmark_rows = _rows(bench_raw, list(BENCHMARK_TICKERS), observed_at, 'benchmark', max_session_date)
    pit_rows = security_rows + benchmark_rows

    # Immutable prospective ledger: provider revisions on later runs cannot
    # rewrite an observation that was already stored for ticker/date.
    conn.executemany(
        '''INSERT OR IGNORE INTO market_pit
           (ticker,date,adjusted_close,volume,observed_at,source,series_type)
           VALUES(?,?,?,?,?,?,?)''', pit_rows
    )

    # Legacy table remains for the existing dashboard during migration. It now
    # uses the same adjusted-close convention, but is NOT the experimental source
    # of truth. New outcome code must read market_pit.
    legacy_rows = [(t,d,c,v,None) for t,d,c,v,_,_,_ in pit_rows]
    conn.executemany(
        '''INSERT INTO market(ticker,date,close,volume,market_cap)
           VALUES(?,?,?,?,?)
           ON CONFLICT(ticker,date) DO UPDATE SET close=excluded.close, volume=excluded.volume''',
        legacy_rows
    )
    conn.commit()
    conn.close()
    return len(pit_rows)
