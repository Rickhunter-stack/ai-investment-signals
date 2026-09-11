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
    latest, history, outcomes, theses = {}, {}, [], {}
    if not DB.exists():
        return latest, history, outcomes, theses
    conn = sqlite3.connect(DB)
    try:
        market_rows = conn.execute(
            'SELECT ticker,date,close FROM market WHERE close IS NOT NULL ORDER BY ticker,date'
        ).fetchall()
        for ticker, date, close in market_rows:
            history.setdefault(ticker, []).append({'date': date, 'close': close})
            latest[ticker] = {'date': date, 'close': close}

        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        if 'theses' in tables:
            thesis_rows = conn.execute('''
                SELECT ticker, created_at, thesis, catalyst, falsification, status,
                       industrial_score, financial_score, criticality_score,
                       valuation_score, evidence_diversity_score
                FROM theses
                ORDER BY ticker, created_at
            ''').fetchall()
            keys = ['ticker','created_at','thesis','catalyst','falsification','status',
                    'industrial_score','financial_score','criticality_score',
                    'valuation_score','evidence_diversity_score']
            for r in thesis_rows:
                item = dict(zip(keys, r))
                theses[item['ticker']] = item

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
            keys = ['ticker','created_at','industrial_score','financial_score','criticality_score',
                    'valuation_score','evidence_diversity_score','horizon','excess_return']
            outcomes = [dict(zip(keys, r)) for r in outcome_rows]
    finally:
        conn.close()
    return latest, history, outcomes, theses


def build():
    universe = load_universe()
    latest, history, outcomes, theses = load_data()
    themes = {
        'ai_semi': 'IA / semi-conducteurs',
        'robotics': 'Robotique',
        'biotech_medtech': 'Biotech / medtech',
    }

    rows = []
    for u in universe:
        m = latest.get(u['ticker'], {})
        t = theses.get(u['ticker'], {})
        rows.append({
            **u,
            'theme_label': themes.get(u['theme'], u['theme']),
            'date': m.get('date', ''),
            'close': m.get('close'),
            'thesis_data': t,
        })

    counts = {
        'all': len(rows),
        'anchor': sum(r['role'] == 'anchor' for r in rows),
        'enabler': sum(r['role'] != 'anchor' for r in rows),
    }
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

    def esc(v):
        return html.escape(str(v or ''))

    table_rows = ''.join(
        f'''<tr data-theme="{esc(r['theme'])}" data-role="{esc(r['role'])}" data-ticker="{esc(r['ticker'])}">
        <td class="ticker">{esc(r['ticker'])}</td><td>{esc(r['company'])}</td>
        <td>{esc(r['theme_label'])}</td><td><span class="pill {esc(r['role'])}">{esc(r['role'])}</span></td>
        <td>{esc(r['subtheme']).replace('_',' ')}</td>
        <td class="num">{'' if r['close'] is None else f'{r["close"]:.2f}'}</td><td>{esc(r['date'])}</td></tr>'''
        for r in rows
    )

    rows_json = json.dumps(rows, ensure_ascii=False)
    history_json = json.dumps(history, ensure_ascii=False)
    outcomes_json = json.dumps(outcomes, ensure_ascii=False)

    page = f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Investment Signals</title><link rel="icon" href="/favicon.svg" type="image/svg+xml">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<style>
:root{{--bg:#0d1214;--panel:#151d20;--panel2:#1b2629;--ink:#edf3f2;--muted:#91a1a1;--rule:#2a383b;--accent:#5fc4cb;--green:#6fc08d;--amber:#dbb05a;--blue:#93aee0;--red:#df7c72}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 Inter,system-ui,Arial,sans-serif}}
.app{{display:grid;grid-template-columns:300px minmax(0,1fr);min-height:100vh}}.sidebar{{position:sticky;top:0;height:100vh;border-right:1px solid var(--rule);background:#101719;padding:22px 14px;overflow:auto}}.main{{min-width:0;padding:28px 34px 70px}}
.brand{{padding:0 8px 18px;border-bottom:1px solid var(--rule)}}.eyebrow{{text-transform:uppercase;letter-spacing:.13em;font-size:.68rem;color:var(--accent);font-weight:800}}.brand h1{{font-size:1.28rem;margin:5px 0 4px}}.brand p,.muted{{color:var(--muted)}}
.search{{width:100%;margin:16px 0 10px;background:var(--panel);border:1px solid var(--rule);color:var(--ink);border-radius:9px;padding:10px 11px;outline:none}}.search:focus{{border-color:var(--accent)}}
.sidefilters{{display:flex;gap:5px;flex-wrap:wrap;margin-bottom:12px}}button,.chip,select{{background:var(--panel2);color:var(--ink);border:1px solid var(--rule);border-radius:999px;padding:7px 10px;cursor:pointer}}button.active,.chip.active{{border-color:var(--accent);color:var(--accent)}}
.navgroup{{margin:17px 0 7px;padding:0 8px;color:var(--muted);font-size:.68rem;text-transform:uppercase;letter-spacing:.1em;font-weight:800}}.tickerbtn{{display:grid;grid-template-columns:1fr auto;gap:4px;width:100%;text-align:left;border-radius:9px;padding:9px 10px;margin:3px 0;background:transparent;border:1px solid transparent}}.tickerbtn:hover{{background:var(--panel)}}.tickerbtn.active{{background:var(--panel2);border-color:var(--accent)}}.tickerbtn b{{color:var(--accent)}}.tickerbtn small{{grid-column:1/-1;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}.price{{font-variant-numeric:tabular-nums}}
.topbar{{display:flex;justify-content:space-between;gap:20px;align-items:flex-start;border-bottom:1px solid var(--rule);padding-bottom:20px;margin-bottom:20px}}.titleblock h2{{font-size:clamp(2rem,4vw,3.5rem);margin:2px 0 7px;line-height:1}}.meta{{display:flex;gap:8px;flex-wrap:wrap}}.pill{{font-size:.7rem;padding:4px 8px;border-radius:999px;border:1px solid var(--rule)}}.anchor{{color:var(--blue)}}.enabler{{color:var(--green)}}.emerging{{color:var(--amber)}}
.kpis{{display:grid;grid-template-columns:repeat(4,minmax(130px,1fr));gap:9px;margin:0 0 18px}}.kpi,.card{{background:var(--panel);border:1px solid var(--rule);border-radius:11px}}.kpi{{padding:14px}}.kpi b{{font-size:1.35rem;display:block}}.kpi span{{color:var(--muted);font-size:.75rem}}
.workspace{{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(330px,.75fr);gap:14px}}.card{{padding:16px}}.card h3{{margin:0 0 12px;font-size:1rem}}.chartbox{{height:390px;position:relative}}.scoregrid{{display:grid;grid-template-columns:1fr 1fr;gap:8px}}.score{{background:var(--panel2);border:1px solid var(--rule);border-radius:9px;padding:11px}}.score b{{font-size:1.3rem;display:block}}.score span{{color:var(--muted);font-size:.72rem}}.score.empty b{{color:var(--muted)}}
.thesis{{margin-top:12px;border-top:1px solid var(--rule);padding-top:12px}}.thesis strong{{display:block;margin-top:9px;font-size:.78rem}}.thesis p{{margin:4px 0;color:#cad4d3}}.emptyState{{color:var(--muted);padding:20px 0}}
.lab{{margin-top:14px;display:grid;grid-template-columns:1fr 1fr;gap:14px}}.controls{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px}}select{{border-radius:8px}}
.details{{margin-top:22px}}details{{background:var(--panel);border:1px solid var(--rule);border-radius:11px;padding:12px 14px}}summary{{cursor:pointer;font-weight:700}}.tablewrap{{overflow:auto;margin-top:12px}}table{{border-collapse:collapse;width:100%;min-width:820px}}th,td{{padding:10px 12px;border-bottom:1px solid var(--rule);text-align:left}}th{{font-size:.68rem;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}}.ticker{{color:var(--accent);font-weight:800}}.num{{text-align:right;font-variant-numeric:tabular-nums}}
@media(max-width:1000px){{.app{{grid-template-columns:240px minmax(0,1fr)}}.main{{padding:22px 20px}}.workspace,.lab{{grid-template-columns:1fr}}.kpis{{grid-template-columns:1fr 1fr}}}}
@media(max-width:720px){{.app{{display:block}}.sidebar{{position:relative;height:auto;border-right:0;border-bottom:1px solid var(--rule)}}#tickerNav{{max-height:270px;overflow:auto}}.main{{padding:20px 14px}}.topbar{{display:block}}.kpis{{grid-template-columns:1fr 1fr}}}}
</style></head><body><div class="app">
<aside class="sidebar"><div class="brand"><div class="eyebrow">Radar prospectif</div><h1>AI Investment Signals</h1><p>IA · Robotique · Biotech</p></div>
<input id="search" class="search" placeholder="Rechercher une valeur...">
<div class="sidefilters" id="sidefilters"><button class="active" data-theme="all">Tout</button><button data-theme="ai_semi">IA</button><button data-theme="robotics">Robotique</button><button data-theme="biotech_medtech">Biotech</button></div>
<div id="tickerNav"></div></aside>
<main class="main">
<div class="topbar"><div class="titleblock"><div class="eyebrow" id="themeLabel">Radar</div><h2><span id="companyName">Sélection</span> <span class="muted" id="tickerLabel"></span></h2><div class="meta"><span id="rolePill" class="pill"></span><span class="pill" id="subthemeLabel"></span><span class="pill" id="lastDate"></span></div></div><div><div class="muted">Dashboard généré</div><b>{now}</b></div></div>
<div class="kpis"><div class="kpi"><b>{counts['all']}</b><span>Sociétés suivies</span></div><div class="kpi"><b>{counts['anchor']}</b><span>Anchors / blockbusters</span></div><div class="kpi"><b>{counts['enabler']}</b><span>Enablers / emerging</span></div><div class="kpi"><b id="currentPrice">-</b><span>Cours sélectionné</span></div></div>
<div class="workspace"><section class="card"><h3>Cotation et événements</h3><div class="chartbox"><canvas id="priceChart"></canvas></div></section><aside class="card"><h3>Indicateurs de thèse</h3><div class="scoregrid" id="scoreGrid"></div><div class="thesis" id="thesisBox"></div></aside></div>
<div class="lab"><section class="card"><h3>Corrélation prospective</h3><div class="controls"><label>Indicateur <select id="indicatorSelect"><option value="industrial_score">Signal industriel</option><option value="financial_score">Confirmation financière</option><option value="criticality_score">Criticité</option><option value="valuation_score">Valorisation</option><option value="evidence_diversity_score">Diversité des preuves</option></select></label><label>Horizon <select id="horizonSelect"><option>M1</option><option>M3</option><option selected>M6</option><option>M12</option></select></label></div><div class="chartbox"><canvas id="corrChart"></canvas></div><p class="muted" id="corrNote"></p></section><section class="card"><h3>Lecture du dossier</h3><div id="readout" class="emptyState">Sélectionne une société dans la colonne de gauche.</div></section></div>
<div class="details"><details><summary>Voir l'univers complet ({counts['all']} valeurs)</summary><div class="tablewrap"><table><thead><tr><th>Ticker</th><th>Société</th><th>Thème</th><th>Rôle</th><th>Maillon</th><th class="num">Cours</th><th>Date</th></tr></thead><tbody>{table_rows}</tbody></table></div></details></div>
</main></div>
<script>
const ROWS={rows_json}; const HISTORY={history_json}; const OUTCOMES={outcomes_json};
const byTicker=Object.fromEntries(ROWS.map(r=>[r.ticker,r]));
const themeNames={{ai_semi:'IA / semi-conducteurs',robotics:'Robotique',biotech_medtech:'Biotech / medtech'}};
let selected=ROWS[0]?.ticker||''; let themeFilter='all'; let priceChart,corrChart;
function fmtPrice(v){{return v==null?'-':Number(v).toLocaleString('fr-FR',{{minimumFractionDigits:2,maximumFractionDigits:2}})}}
function buildNav(){{const q=document.getElementById('search').value.toLowerCase();const nav=document.getElementById('tickerNav');nav.innerHTML='';const visible=ROWS.filter(r=>(themeFilter==='all'||r.theme===themeFilter)&&(`${{r.ticker}} ${{r.company}} ${{r.subtheme}}`.toLowerCase().includes(q)));const groups=[['anchor','Anchors / blockbusters'],['enabler','Critical enablers'],['emerging','Emerging']];groups.forEach(([role,label])=>{{const items=visible.filter(r=>r.role===role);if(!items.length)return;const h=document.createElement('div');h.className='navgroup';h.textContent=label;nav.appendChild(h);items.forEach(r=>{{const b=document.createElement('button');b.className='tickerbtn'+(r.ticker===selected?' active':'');b.innerHTML=`<b>${{r.ticker}}</b><span class="price">${{fmtPrice(r.close)}}</span><small>${{r.company}} · ${{r.subtheme.replaceAll('_',' ')}}</small>`;b.onclick=()=>selectTicker(r.ticker);nav.appendChild(b)}})}})}}
function scoreCard(label,v){{const empty=v==null;return `<div class="score ${{empty?'empty':''}}"><b>${{empty?'–':Number(v).toFixed(0)}}</b><span>${{label}}</span></div>`}}
function selectTicker(t){{selected=t;const r=byTicker[t];if(!r)return;document.getElementById('companyName').textContent=r.company;document.getElementById('tickerLabel').textContent=`(${{r.ticker}})`;document.getElementById('themeLabel').textContent=r.theme_label;const rp=document.getElementById('rolePill');rp.textContent=r.role;rp.className='pill '+r.role;document.getElementById('subthemeLabel').textContent=r.subtheme.replaceAll('_',' ');document.getElementById('lastDate').textContent=r.date||'Pas de cotation';document.getElementById('currentPrice').textContent=fmtPrice(r.close);const td=r.thesis_data||{{}};document.getElementById('scoreGrid').innerHTML=scoreCard('Signal industriel',td.industrial_score)+scoreCard('Confirmation financière',td.financial_score)+scoreCard('Criticité',td.criticality_score)+scoreCard('Valorisation',td.valuation_score)+scoreCard('Diversité des preuves',td.evidence_diversity_score);document.getElementById('thesisBox').innerHTML=td.thesis?`<strong>Thèse figée</strong><p>${{td.thesis}}</p><strong>Catalyseur</strong><p>${{td.catalyst||'Non renseigné'}}</p><strong>Falsification</strong><p>${{td.falsification||'Non renseignée'}}</p>`:'<div class="emptyState">Aucune thèse figée pour cette valeur pour le moment.</div>';document.getElementById('readout').innerHTML=`<b>${{r.company}}</b><p class="muted">${{r.theme_label}} · ${{r.role}} · ${{r.subtheme.replaceAll('_',' ')}}</p><p>La fiche va progressivement agréger preuves primaires, événements, relations clients-fournisseurs, catalyseurs et conditions de falsification.</p>`;drawPrice();buildNav()}}
function drawPrice(){{const pts=HISTORY[selected]||[];if(priceChart)priceChart.destroy();priceChart=new Chart(document.getElementById('priceChart'),{{type:'line',data:{{labels:pts.map(x=>x.date),datasets:[{{label:selected,data:pts.map(x=>x.close),borderColor:'#5fc4cb',backgroundColor:'rgba(95,196,203,.10)',fill:true,tension:.18,pointRadius:0,borderWidth:2}}]}},options:{{responsive:true,maintainAspectRatio:false,interaction:{{mode:'index',intersect:false}},plugins:{{legend:{{labels:{{color:'#edf3f2'}}}}}},scales:{{x:{{ticks:{{color:'#91a1a1',maxTicksLimit:9}},grid:{{color:'#243033'}}}},y:{{ticks:{{color:'#91a1a1'}},grid:{{color:'#243033'}}}}}}}}}})}}
function drawCorr(){{const metric=document.getElementById('indicatorSelect').value,horizon=document.getElementById('horizonSelect').value;const pts=OUTCOMES.filter(x=>x.horizon===horizon&&x[metric]!=null&&x.excess_return!=null).map(x=>({{x:x[metric],y:x.excess_return,ticker:x.ticker}}));if(corrChart)corrChart.destroy();corrChart=new Chart(document.getElementById('corrChart'),{{type:'scatter',data:{{datasets:[{{label:`${{metric}} vs excès ${{horizon}}`,data:pts,backgroundColor:'#dbb05a',pointRadius:5}}]}},options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{labels:{{color:'#edf3f2'}}}},tooltip:{{callbacks:{{label:c=>`${{c.raw.ticker}} : ${{c.raw.x}} / ${{(c.raw.y*100).toFixed(1)}}%`}}}}}},scales:{{x:{{ticks:{{color:'#91a1a1'}},grid:{{color:'#243033'}}}},y:{{ticks:{{color:'#91a1a1',callback:v=>(v*100)+'%'}},grid:{{color:'#243033'}}}}}}}}}});document.getElementById('corrNote').textContent=pts.length<5?'Échantillon encore insuffisant : aucune conclusion statistique.':`${{pts.length}} observations disponibles. Comparer Pearson et Spearman avant interprétation.`}}
document.getElementById('search').oninput=buildNav;document.querySelectorAll('#sidefilters button').forEach(b=>b.onclick=()=>{{document.querySelectorAll('#sidefilters button').forEach(x=>x.classList.remove('active'));b.classList.add('active');themeFilter=b.dataset.theme;buildNav()}});document.getElementById('indicatorSelect').onchange=drawCorr;document.getElementById('horizonSelect').onchange=drawCorr;buildNav();selectTicker(selected);drawCorr();
</script></body></html>'''
    OUT.write_text(page, encoding='utf-8')
    print(OUT)


if __name__ == '__main__':
    build()
