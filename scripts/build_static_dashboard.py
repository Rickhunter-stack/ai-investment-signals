from pathlib import Path
import csv, sqlite3, html, json
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'data' / 'veille.db'
UNIVERSE = ROOT / 'data' / 'universe_seed.csv'
OUT = ROOT / 'index.html'


def load_universe():
    with open(UNIVERSE, encoding='utf-8') as f:
        return list(csv.DictReader(f))


def load_data():
    latest, history, outcomes = {}, {}, []
    if not DB.exists():
        return latest, history, outcomes
    conn = sqlite3.connect(DB)
    try:
        market_rows = conn.execute('SELECT ticker,date,close FROM market WHERE close IS NOT NULL ORDER BY ticker,date').fetchall()
        for ticker, date, close in market_rows:
            history.setdefault(ticker, []).append({'date': date, 'close': close})
            latest[ticker] = {'date': date, 'close': close}

        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        if {'theses', 'signal_outcomes'}.issubset(tables):
            outcome_rows = conn.execute('''
                SELECT t.ticker, t.created_at,
                       t.industrial_score, t.financial_score, t.criticality_score,
                       t.valuation_score, t.evidence_diversity_score,
                       o.horizon, o.excess_return
                FROM theses t
                JOIN signal_outcomes o ON o.thesis_id=t.id
                WHERE o.excess_return IS NOT NULL
                ORDER BY t.created_at
            ''').fetchall()
            keys = ['ticker','created_at','industrial_score','financial_score','criticality_score','valuation_score','evidence_diversity_score','horizon','excess_return']
            outcomes = [dict(zip(keys, r)) for r in outcome_rows]
    finally:
        conn.close()
    return latest, history, outcomes


def build():
    universe = load_universe()
    latest, history, outcomes = load_data()
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
        f'''<tr data-theme="{esc(r['theme'])}" data-role="{esc(r['role'])}" data-ticker="{esc(r['ticker'])}">
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
    default_tickers = [r['ticker'] for r in rows[:5]]

    history_json = json.dumps(history, ensure_ascii=False)
    outcomes_json = json.dumps(outcomes, ensure_ascii=False)
    tickers_json = json.dumps(default_tickers)

    page = f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Investment Signals</title>
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<style>
:root{{--bg:#0f1416;--panel:#161e20;--panel2:#1e282a;--ink:#e8eeed;--muted:#95a4a3;--rule:#2b3739;--accent:#5fc4cb;--green:#6fc08d;--amber:#dbb05a;--blue:#93aee0}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 Inter,system-ui,Arial,sans-serif}}.wrap{{max-width:1280px;margin:auto;padding:36px 22px 80px}}
header{{border-bottom:1px solid var(--rule);padding-bottom:24px;margin-bottom:26px}}h1{{font-size:clamp(2rem,5vw,4rem);line-height:1;margin:8px 0 10px}}h2{{margin-top:34px}}.eyebrow{{text-transform:uppercase;letter-spacing:.14em;font-size:.72rem;color:var(--accent);font-weight:800}}.sub{{color:var(--muted);max-width:820px}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin:24px 0}}.kpi,.chartcard{{background:var(--panel);border:1px solid var(--rule);padding:16px;border-radius:10px}}.kpi b{{font-size:1.7rem;display:block}}.kpi span,.muted{{color:var(--muted);font-size:.8rem}}
.controls{{display:flex;gap:10px;flex-wrap:wrap;margin:18px 0}}button,select{{background:var(--panel2);color:var(--ink);border:1px solid var(--rule);padding:8px 12px;border-radius:999px;cursor:pointer}}button.active{{border-color:var(--accent);color:var(--accent)}}
.charts{{display:grid;grid-template-columns:1.4fr 1fr;gap:14px;margin:14px 0 28px}}.chartbox{{height:340px;position:relative}}@media(max-width:900px){{.charts{{grid-template-columns:1fr}}}}
.tablewrap{{overflow:auto;background:var(--panel);border:1px solid var(--rule);border-radius:12px}}table{{border-collapse:collapse;width:100%;min-width:860px}}th,td{{padding:11px 14px;border-bottom:1px solid var(--rule);text-align:left}}th{{position:sticky;top:0;background:var(--panel2);font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}}tr:hover{{background:var(--panel2)}}.ticker{{color:var(--accent);font-weight:800}}.num{{text-align:right;font-variant-numeric:tabular-nums}}.pill{{font-size:.7rem;padding:4px 8px;border-radius:999px;border:1px solid var(--rule)}}.anchor{{color:var(--blue)}}.enabler{{color:var(--green)}}.emerging{{color:var(--amber)}}
.note{{margin-top:22px;color:var(--muted);font-size:.86rem}}footer{{margin-top:38px;border-top:1px solid var(--rule);padding-top:18px;color:var(--muted);font-size:.8rem}}
</style></head><body><div class="wrap">
<header><div class="eyebrow">Radar prospectif · IA · Robotique · Biotech</div><h1>AI Investment Signals</h1><p class="sub">Suivi des blockbusters, anchors et sous-traitants critiques. Le système cherche ce qui vient de changer dans les chaînes de valeur, sans transformer un score en recommandation d'achat.</p></header>
<div class="kpis"><div class="kpi"><b>{counts['all']}</b><span>Sociétés suivies</span></div><div class="kpi"><b>{counts['anchor']}</b><span>Anchors / blockbusters</span></div><div class="kpi"><b>{counts['enabler']}</b><span>Enablers / emerging</span></div><div class="kpi"><b>{now}</b><span>Génération du dashboard</span></div></div>

<h2>Marché & laboratoire d'indicateurs</h2>
<div class="charts">
  <div class="chartcard"><div class="controls"><label>Valeur <select id="tickerSelect"></select></label></div><div class="chartbox"><canvas id="priceChart"></canvas></div></div>
  <div class="chartcard"><div class="controls"><label>Indicateur <select id="indicatorSelect"><option value="industrial_score">Signal industriel</option><option value="financial_score">Confirmation financière</option><option value="criticality_score">Criticité</option><option value="valuation_score">Valorisation</option><option value="evidence_diversity_score">Diversité des preuves</option></select></label><label>Horizon <select id="horizonSelect"><option>M1</option><option>M3</option><option selected>M6</option><option>M12</option></select></label></div><div class="chartbox"><canvas id="corrChart"></canvas></div><p class="muted" id="corrNote"></p></div>
</div>

<div class="controls" id="filters"><button class="active" data-filter="all">Tout</button><button data-filter="ai_semi">IA / Semi</button><button data-filter="robotics">Robotique</button><button data-filter="biotech_medtech">Biotech / Medtech</button><button data-role="enabler">Critical enablers</button><button data-role="anchor">Anchors</button></div>
<div class="tablewrap"><table><thead><tr><th>Ticker</th><th>Société</th><th>Thème</th><th>Rôle</th><th>Maillon</th><th class="num">Cours</th><th>Date</th></tr></thead><tbody>{cards}</tbody></table></div>
<p class="note">Le nuage de points compare un indicateur figé à la date du signal avec la performance future excédentaire. Il restera volontairement vide tant qu'un horizon n'est pas réellement atteint.</p>
<footer>Outil de veille personnelle. Aucune recommandation d'achat ou de vente.</footer>
</div><script>
const HISTORY={history_json};
const OUTCOMES={outcomes_json};
const DEFAULT_TICKERS={tickers_json};
const buttons=[...document.querySelectorAll('#filters button')], rows=[...document.querySelectorAll('tbody tr')];
buttons.forEach(b=>b.onclick=()=>{{buttons.forEach(x=>x.classList.remove('active'));b.classList.add('active');const f=b.dataset.filter,r=b.dataset.role;rows.forEach(tr=>{{tr.style.display=(f==='all'||tr.dataset.theme===f||r&&tr.dataset.role===r)?'':'none'}})}});

const tickerSelect=document.getElementById('tickerSelect');
Object.keys(HISTORY).sort().forEach(t=>{{const o=document.createElement('option');o.value=o.textContent=t;tickerSelect.appendChild(o)}});
if(DEFAULT_TICKERS.length && HISTORY[DEFAULT_TICKERS[0]]) tickerSelect.value=DEFAULT_TICKERS[0];
let priceChart;
function drawPrice(){{
  const t=tickerSelect.value, pts=HISTORY[t]||[];
  if(priceChart) priceChart.destroy();
  priceChart=new Chart(document.getElementById('priceChart'),{{type:'line',data:{{labels:pts.map(x=>x.date),datasets:[{{label:t,data:pts.map(x=>x.close),borderColor:'#5fc4cb',backgroundColor:'rgba(95,196,203,.12)',fill:true,tension:.18,pointRadius:0}}]}},options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:true,labels:{{color:'#e8eeed'}}}}}},scales:{{x:{{ticks:{{color:'#95a4a3',maxTicksLimit:8}},grid:{{color:'#2b3739'}}}},y:{{ticks:{{color:'#95a4a3'}},grid:{{color:'#2b3739'}}}}}}}}}});
}}
tickerSelect.onchange=drawPrice; drawPrice();

let corrChart;
function drawCorr(){{
  const metric=document.getElementById('indicatorSelect').value, horizon=document.getElementById('horizonSelect').value;
  const pts=OUTCOMES.filter(x=>x.horizon===horizon && x[metric]!==null && x.excess_return!==null).map(x=>({{x:x[metric],y:x.excess_return,ticker:x.ticker}}));
  if(corrChart) corrChart.destroy();
  corrChart=new Chart(document.getElementById('corrChart'),{{type:'scatter',data:{{datasets:[{{label:`${{metric}} vs excès ${{horizon}}`,data:pts,backgroundColor:'#dbb05a',pointRadius:5}}]}},options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{labels:{{color:'#e8eeed'}}}},tooltip:{{callbacks:{{label:(c)=>`${{c.raw.ticker}} : indicateur ${{c.raw.x}} / excès ${{(c.raw.y*100).toFixed(1)}}%`}}}}}},scales:{{x:{{title:{{display:true,text:'Indicateur au signal',color:'#95a4a3'}},ticks:{{color:'#95a4a3'}},grid:{{color:'#2b3739'}}}},y:{{title:{{display:true,text:'Performance excédentaire',color:'#95a4a3'}},ticks:{{color:'#95a4a3',callback:v=>(v*100)+'%'}},grid:{{color:'#2b3739'}}}}}}}}}});
  document.getElementById('corrNote').textContent=pts.length<5?'Échantillon encore insuffisant : aucune conclusion statistique.':'Comparer Pearson et Spearman avant toute interprétation.';
}}
document.getElementById('indicatorSelect').onchange=drawCorr;document.getElementById('horizonSelect').onchange=drawCorr;drawCorr();
</script></body></html>'''
    OUT.write_text(page, encoding='utf-8')
    print(OUT)

if __name__ == '__main__':
    build()
