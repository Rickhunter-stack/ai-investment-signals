
from pathlib import Path
import csv, html

ROOT = Path(__file__).resolve().parents[1]
signals = ROOT / "data" / "signals.csv"
universe = ROOT / "data" / "universe.csv"
out = ROOT / "reports" / "dashboard.html"

def read_csv(path):
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))

u = read_csv(universe)
s = read_csv(signals)

rows = []
for item in u:
    ticker = item["ticker"]
    ticker_signals = [x for x in s if x.get("ticker")==ticker]
    latest = ticker_signals[-1] if ticker_signals else {}
    rows.append({
        "ticker": ticker,
        "company": item["company"],
        "theme": item["theme"],
        "score": latest.get("signal_score",""),
        "headline": latest.get("headline",""),
        "date": latest.get("date","")
    })

trs = "\n".join(
    f"<tr><td>{html.escape(r['ticker'])}</td><td>{html.escape(r['company'])}</td>"
    f"<td>{html.escape(r['theme'])}</td><td>{html.escape(r['score'])}</td>"
    f"<td>{html.escape(r['date'])}</td><td>{html.escape(r['headline'])}</td></tr>"
    for r in rows
)

page = f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><title>AI Investment Signals</title>
<style>
body{{font-family:Arial,sans-serif;max-width:1200px;margin:40px auto;padding:0 20px}}
table{{width:100%;border-collapse:collapse}} th,td{{padding:10px;border-bottom:1px solid #ddd;text-align:left}}
th{{position:sticky;top:0;background:#fff}}
.score{{font-size:2rem;font-weight:700}}
</style></head><body>
<h1>AI Investment Signals</h1>
<p>Dashboard prospectif. Les scores historiques ne doivent jamais être réécrits.</p>
<table><thead><tr><th>Ticker</th><th>Entreprise</th><th>Thème</th><th>Score</th><th>Date</th><th>Dernier signal</th></tr></thead>
<tbody>{trs}</tbody></table>
</body></html>"""

out.write_text(page, encoding="utf-8")
print(out)
