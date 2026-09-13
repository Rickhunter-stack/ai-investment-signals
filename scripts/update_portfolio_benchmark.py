from pathlib import Path
from datetime import datetime, timezone
import json
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
PORTFOLIO = ROOT / 'data' / 'portfolio.json'
OUT = ROOT / 'data' / 'benchmark_history.json'


def main():
    cfg = json.loads(PORTFOLIO.read_text(encoding='utf-8'))
    ticker = cfg['benchmark']['ticker']
    inception = cfg['inception_date']
    existing = {'ticker': ticker, 'label': cfg['benchmark']['label'], 'prices': []}
    if OUT.exists():
        try:
            existing = json.loads(OUT.read_text(encoding='utf-8'))
        except Exception:
            pass
    known = {p['date']: p for p in existing.get('prices', [])}
    frame = yf.download(ticker, period='1mo', interval='1d', auto_adjust=True, repair=True, progress=False)
    if not frame.empty:
        close = frame['Close']
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        for idx, value in close.dropna().items():
            date = idx.date().isoformat()
            if date >= inception:
                known[date] = {'date': date, 'value': round(float(value), 6)}
    payload = {
        'ticker': ticker,
        'label': cfg['benchmark']['label'],
        'updated_at': datetime.now(timezone.utc).isoformat(),
        'prices': [known[d] for d in sorted(known)]
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f"Benchmark {ticker}: {len(payload['prices'])} observations")


if __name__ == '__main__':
    main()
