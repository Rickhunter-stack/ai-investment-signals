from pathlib import Path
import csv, sqlite3, html
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'data' / 'veille.db'
UNIVERSE = ROOT / 'data' / 'universe_seed.csv'
OUT = ROOT / 'index.html'


def load_universe():
    with open(UNIVERSE, encoding='utf-8') as f:
        return list(csv.DictReader(f))


def load_latest_market():
    if not DB.exists():
        return {}
    conn = sqlite3.connect(DB)
    try:
        rows = conn.execute('''
            SELECT m.ticker, m.date, m.close, m.volume
            FROM market m
            JOIN (
                SELECT ticker, MAX(date) AS max_date FROM market GROUP BY ticker
            ) x ON x.ticker=m.ticker AND x.max_date=m.date
        ''').fetchall()
        return {r[0]: {'date': r[1], 'close': r[2], 'volume': r[3]} for r in rows}
    finally:
        conn.close()


def build():
    universe = load_universe()
    latest = load_latest_market()
    themes = {
        'ai_semi': 'IA / semi-conducteurs',
        'robotics': 'Robotique',
        'biotech_medtech': 'Biotech / medtech',
    }

    rows = []
    for u in universe:
        m = latest.get(u['ticker'], {})
        close = '' if m.get('close') is None else f"{m['close']:.2f}"
        rows.append({**u, 'date': m.get('date',''), 'close': close})

    def esc(v): return html.escape(str(v or ''))
    cards = ''.join(
        f'''<tr data-theme="{esc(r['theme'])}" data-role="{esc(r['role'])}">
        <td class="ticker">{esc(r['ticker'])}</td>
        <td>{esc(r['company'])}</td>
        <td>{esc(themes.get(r['theme'], r['theme']))}</td>
        <td><span class="pill {esc(r['role'])}">{esc(r['role'])}</span></td>
        <td>{esc(r['subtheme']).replace('_',' ')}</td>
        <td class="num">{esc(r['close'])}</td>
        <td>{esc(r['date'])}</td></tr>'''
        for r in rows
    )

    counts = {
        'all': len(rows),
        'anchor': sum(r['role']=='anchor' for r in rows),
        'enabler': sum(r['role']!='anchor' for r in rows),
    }
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

    page = f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Investment Signals</title>
<style>
:root{{--bg:#0f1416;--panel:#161e20;--panel2:#1e282a;--ink:#e8eeed;--muted:#95a4a3;--rule:#2b3739;--accent:#5fc4cb;--green:#6fc08d;--amber:#dbb05a;--blue:#93aee0}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 Inter,system-ui,Arial,sans-serif}}.wrap{{max-width:1280px;margin:auto;padding:36px 22px 80px}}
header{{border-bottom:1px solid var(--rule);padding-bottom:24px;margin-bottom:26px}}h1{{font-size:clamp(2rem,5vw,4rem);line-height:1;margin:8px 0 10px}}.eyebrow{{text-transform:uppercase;letter-spacing:.14em;font-size:.72rem;color:var(--accent);font-weight:800}}.sub{{color:var(--muted);max-width:820px}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin:24px 0}}.kpi{{background:var(--panel);border:1px solid var(--rule);padding:16px;border-radius:10px}}.kpi b{{font-size:1.7rem;display:block}}.kpi span{{color:var(--muted);font-size:.8rem}}
.controls{{display:flex;gap:10px;flex-wrap:wrap;margin:18px 0}}button{{background:var(--panel2);color:var(--ink);border:1px solid var(--rule);padding:8px 12px;border-radius:999px;cursor:pointer}}button.active{{border-color:var(--accent);color:var(--accent)}}
.tablewrap{{overflow:auto;background:var(--panel);border:1px solid var(--rule);border-radius:12px}}table{{border-collapse:collapse;width:100%;min-width:860px}}th,td{{padding:11px 14px;border-bottom:1px solid var(--rule);text-align:left}}th{{position:sticky;top:0;background:var(--panel2);font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}}tr:hover{{background:var(--panel2)}}.ticker{{color:var(--accent);font-weight:800}}.num{{text-align:right;font-variant-numeric:tabular-nums}}.pill{{font-size:.7rem;padding:4px 8px;border-radius:999px;border:1px solid var(--rule)}}.anchor{{color:var(--blue)}}.enabler{{color:var(--green)}}.emerging{{color:var(--amber)}}
.note{{margin-top:22px;color:var(--muted);font-size:.86rem}}footer{{margin-top:38px;border-top:1px solid var(--rule);padding-top:18px;color:var(--muted);font-size:.8rem}}
</style></head><body><div class="wrap">
<header><div class="eyebrow">Radar prospectif · IA · Robotique · Biotech</div><h1>AI Investment Signals</h1><p class="sub">Suivi des blockbusters, anchors et sous-traitants critiques. Le système cherche ce qui vient de changer dans les chaînes de valeur, sans transformer un score en recommandation d'achat.</p></header>
<div class="kpis"><div class="kpi"><b>{counts['all']}</b><span>Sociétés suivies</span></div><div class="kpi"><b>{counts['anchor']}</b><span>Anchors / blockbusters</span></div><div class="kpi"><b>{counts['enabler']}</b><span>Enablers / emerging</span></div><div class="kpi"><b>{now}</b><span>Génération du dashboard</span></div></div>
<div class="controls" id="filters"><button class="active" data-filter="all">Tout</button><button data-filter="ai_semi">IA / Semi</button><button data-filter="robotics">Robotique</button><button data-filter="biotech_medtech">Biotech / Medtech</button><button data-role="enabler">Critical enablers</button><button data-role="anchor">Anchors</button></div>
<div class="tablewrap"><table><thead><tr><th>Ticker</th><th>Société</th><th>Thème</th><th>Rôle</th><th>Maillon</th><th class="num">Cours</th><th>Date</th></tr></thead><tbody>{cards}</tbody></table></div>
<p class="note">Cette première vue Vercel est statique et auditable. Les prochains blocs ajouteront preuves primaires, événements, relations industrielles, catalyseurs, falsification et performance prospective.</p>
<footer>Outil de veille personnelle. Aucune recommandation d'achat ou de vente.</footer>
</div><script>
const buttons=[...document.querySelectorAll('button')], rows=[...document.querySelectorAll('tbody tr')];
buttons.forEach(b=>b.onclick=()=>{{buttons.forEach(x=>x.classList.remove('active'));b.classList.add('active');const f=b.dataset.filter,r=b.dataset.role;rows.forEach(tr=>{{tr.style.display=(f==='all'||tr.dataset.theme===f||r&&tr.dataset.role===r)?'':'none'}})}});
</script></body></html>'''
    OUT.write_text(page, encoding='utf-8')
    print(OUT)

if __name__ == '__main__':
    build()
