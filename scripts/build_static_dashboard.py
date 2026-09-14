from pathlib import Path
import csv, sqlite3, html, json
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'data' / 'veille.db'
UNIVERSE = ROOT / 'data' / 'universe_seed.csv'
OUT = ROOT / 'index.html'
WEEKLY_SIGNALS = ROOT / 'data' / 'weekly_signals.json'

SIGNAL_COMPONENTS = (
    'fundamental_strength',
    'novelty',
    'pricing_headroom',
    'valuation',
    'execution_risk',
)


def load_universe():
    with open(UNIVERSE, encoding='utf-8') as f:
        return list(csv.DictReader(f))


def load_data():
    latest, history, outcomes, theses = {}, {}, [], {}
    if not DB.exists():
        return latest, history, outcomes, theses
    conn = sqlite3.connect(DB)
    try:
        for ticker, date, close in conn.execute('SELECT ticker,date,close FROM market WHERE close IS NOT NULL ORDER BY ticker,date'):
            history.setdefault(ticker, []).append({'date': date, 'close': close})
            latest[ticker] = {'date': date, 'close': close}
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        if 'theses' in tables:
            keys = ['ticker','created_at','thesis','catalyst','falsification','status','industrial_score','financial_score','criticality_score','valuation_score','evidence_diversity_score']
            for row in conn.execute('''SELECT ticker,created_at,thesis,catalyst,falsification,status,industrial_score,financial_score,criticality_score,valuation_score,evidence_diversity_score FROM theses ORDER BY ticker,created_at'''):
                item = dict(zip(keys, row)); theses[item['ticker']] = item
        if {'theses','signal_outcomes'}.issubset(tables):
            keys = ['ticker','created_at','industrial_score','financial_score','criticality_score','valuation_score','evidence_diversity_score','horizon','excess_return']
            rs = conn.execute('''SELECT t.ticker,t.created_at,t.industrial_score,t.financial_score,t.criticality_score,t.valuation_score,t.evidence_diversity_score,o.horizon,o.excess_return FROM theses t JOIN signal_outcomes o ON o.thesis_id=t.id WHERE o.excess_return IS NOT NULL ORDER BY t.created_at''').fetchall()
            outcomes = [dict(zip(keys, r)) for r in rs]
    finally:
        conn.close()
    return latest, history, outcomes, theses


def load_weekly_signals():
    """Load immutable weekly snapshots and index their latest score by ticker."""
    if not WEEKLY_SIGNALS.exists():
        return [], {}
    snapshots = json.loads(WEEKLY_SIGNALS.read_text(encoding='utf-8'))
    if not isinstance(snapshots, list):
        raise ValueError('data/weekly_signals.json must contain a JSON array')

    latest_by_ticker = {}
    previous_date = ''
    required_score_keys = {'signal_score', *SIGNAL_COMPONENTS}
    for position, snapshot in enumerate(snapshots):
        if not isinstance(snapshot, dict):
            raise ValueError(f'weekly signal snapshot #{position + 1} must be an object')
        missing = {'date', 'frozen', 'method_version', 'scores', 'top3'} - snapshot.keys()
        if missing:
            raise ValueError(f'weekly signal snapshot #{position + 1} is missing: {sorted(missing)}')
        if snapshot['frozen'] is not True:
            raise ValueError(f'weekly signal snapshot {snapshot["date"]!r} must have frozen=true')
        if not snapshot['method_version']:
            raise ValueError(f'weekly signal snapshot {snapshot["date"]!r} needs method_version')
        try:
            datetime.strptime(snapshot['date'], '%Y-%m-%d')
        except (TypeError, ValueError) as exc:
            raise ValueError(f'invalid weekly signal date: {snapshot["date"]!r}') from exc
        if snapshot['date'] <= previous_date:
            raise ValueError('weekly signal snapshots must be append-only with strictly increasing dates')
        previous_date = snapshot['date']
        if not isinstance(snapshot['scores'], dict):
            raise ValueError(f'weekly signal snapshot {snapshot["date"]!r} scores must be keyed by ticker')
        if not isinstance(snapshot['top3'], list) or len(snapshot['top3']) > 3:
            raise ValueError(f'weekly signal snapshot {snapshot["date"]!r} top3 must be an array of at most 3 tickers')
        for ticker, score in snapshot['scores'].items():
            if not isinstance(score, dict) or not required_score_keys.issubset(score):
                raise ValueError(f'incomplete weekly signal score for {ticker} on {snapshot["date"]}')
            latest_by_ticker[ticker] = {
                'date': snapshot['date'],
                'method_version': snapshot['method_version'],
                **{key: score[key] for key in required_score_keys},
            }
    return snapshots, latest_by_ticker


def build():
    themes = {'ai_semi':'IA / semi-conducteurs','robotics':'Robotique','biotech_medtech':'Biotech / medtech'}
    universe = load_universe(); latest, history, outcomes, theses = load_data()
    signal_history, latest_signals = load_weekly_signals()
    rows=[]
    for u in universe:
        m=latest.get(u['ticker'],{}); t=theses.get(u['ticker'],{})
        rows.append({**u,'theme_label':themes.get(u['theme'],u['theme']),'date':m.get('date',''),'close':m.get('close'),'thesis_data':t,'signal_data':latest_signals.get(u['ticker'],{})})
    counts={'all':len(rows),'anchor':sum(r['role']=='anchor' for r in rows),'enabler':sum(r['role']!='anchor' for r in rows)}
    now=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    def esc(v): return html.escape(str(v or ''))
    def pstr(v): return '' if v is None else f'{v:.2f}'
    table=''.join(f'''<tr><td class="ticker">{esc(r['ticker'])}</td><td>{esc(r['company'])}</td><td>{esc(r['theme_label'])}</td><td>{esc(r['role'])}</td><td>{esc(r['subtheme']).replace('_',' ')}</td><td class="num">{pstr(r['close'])}</td><td>{esc(r['date'])}</td></tr>''' for r in rows)
    page=f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AI Investment Signals</title><link rel="icon" href="/favicon.svg" type="image/svg+xml"><script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script><style>
:root{{--bg:#0d1214;--panel:#151d20;--panel2:#1b2629;--ink:#edf3f2;--muted:#91a1a1;--rule:#2a383b;--accent:#5fc4cb;--green:#6fc08d;--amber:#dbb05a;--blue:#93aee0}}
*{{box-sizing:border-box}}html,body{{margin:0;background:var(--bg);color:var(--ink);font:13px/1.35 Inter,system-ui,Arial,sans-serif}}body{{overflow:hidden}}.app{{display:grid;grid-template-columns:255px minmax(0,1fr);height:100vh}}.sidebar{{height:100vh;overflow:auto;border-right:1px solid var(--rule);background:#101719;padding:14px 10px}}.main{{min-width:0;height:100vh;padding:14px 18px;display:grid;grid-template-rows:auto auto minmax(0,1fr);gap:10px;overflow:hidden}}
.brand{{padding:0 6px 10px;border-bottom:1px solid var(--rule)}}.eyebrow{{text-transform:uppercase;letter-spacing:.12em;font-size:.62rem;color:var(--accent);font-weight:800}}.brand h1{{font-size:1.05rem;margin:3px 0}}.muted{{color:var(--muted)}}.search{{width:100%;margin:10px 0 8px;background:var(--panel);border:1px solid var(--rule);color:var(--ink);border-radius:8px;padding:8px}}.sidefilters{{display:flex;gap:4px;flex-wrap:wrap}}button,select{{background:var(--panel2);color:var(--ink);border:1px solid var(--rule);border-radius:999px;padding:5px 8px;cursor:pointer}}button.active{{border-color:var(--accent);color:var(--accent)}}.navgroup{{margin:12px 0 5px;padding:0 7px;color:var(--muted);font-size:.62rem;text-transform:uppercase;letter-spacing:.08em;font-weight:800}}.tickerbtn{{display:grid;grid-template-columns:1fr auto;gap:2px;width:100%;text-align:left;border-radius:8px;padding:7px 8px;margin:2px 0;background:transparent;border:1px solid transparent}}.tickerbtn:hover{{background:var(--panel)}}.tickerbtn.active{{background:var(--panel2);border-color:var(--accent)}}.tickerbtn b{{color:var(--accent)}}.tickerbtn small{{grid-column:1/-1;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:.68rem}}
.topbar{{display:flex;justify-content:space-between;gap:14px;align-items:flex-start;border-bottom:1px solid var(--rule);padding-bottom:8px}}.titleblock h2{{font-size:clamp(1.8rem,3vw,2.7rem);margin:1px 0 5px;line-height:1}}.meta{{display:flex;gap:5px;flex-wrap:wrap}}.pill{{font-size:.62rem;padding:3px 7px;border-radius:999px;border:1px solid var(--rule)}}.kpis{{display:grid;grid-template-columns:repeat(4,minmax(110px,1fr));gap:7px}}.kpi,.card{{background:var(--panel);border:1px solid var(--rule);border-radius:10px}}.kpi{{padding:9px 11px;min-height:54px}}.kpi b{{font-size:1.12rem;display:block}}.kpi span{{color:var(--muted);font-size:.67rem}}
.dashboard{{min-height:0;display:grid;grid-template-columns:minmax(0,1.55fr) minmax(320px,.8fr);grid-template-rows:minmax(0,1fr) minmax(0,.82fr);gap:10px}}.card{{padding:11px;min-height:0;overflow:hidden}}.card h3{{margin:0 0 7px;font-size:.88rem}}.chartbox{{height:calc(100% - 24px);min-height:150px;position:relative}}.pricecard{{grid-column:1;grid-row:1}}.scorecard{{grid-column:2;grid-row:1;overflow:auto}}.corrcard{{grid-column:1;grid-row:2}}.readcard{{grid-column:2;grid-row:2}}.scoregrid{{display:grid;grid-template-columns:1fr 1fr;gap:6px}}.score{{background:var(--panel2);border:1px solid var(--rule);border-radius:8px;padding:8px}}.score b{{font-size:1.08rem;display:block}}.score span{{color:var(--muted);font-size:.65rem}}.signalblock{{padding-bottom:8px;margin-bottom:8px;border-bottom:1px solid var(--rule)}}.signalblock h4{{margin:0 0 6px;font-size:.72rem;color:var(--amber);text-transform:uppercase;letter-spacing:.06em}}.signalgrid .score:first-child{{grid-column:1/-1;border-color:var(--amber)}}.signalgrid .score:first-child b{{font-size:1.4rem;color:var(--amber)}}.thesis{{margin-top:8px;border-top:1px solid var(--rule);padding-top:6px;font-size:.72rem}}.thesis strong{{display:block;margin-top:5px}}.thesis p{{margin:2px 0;color:#cad4d3}}.controls{{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:5px;font-size:.7rem}}select{{border-radius:7px;padding:4px 7px}}.corrwrap{{height:calc(100% - 55px);min-height:115px}}.readcard{{overflow:auto}}.readcard p{{margin:4px 0}}.details{{position:fixed;right:14px;bottom:8px;z-index:20}}details{{background:var(--panel);border:1px solid var(--rule);border-radius:8px;padding:6px 9px;max-width:min(900px,80vw)}}summary{{cursor:pointer;font-weight:700}}.tablewrap{{max-height:45vh;overflow:auto;margin-top:7px}}table{{border-collapse:collapse;width:100%;min-width:760px}}th,td{{padding:7px 9px;border-bottom:1px solid var(--rule);text-align:left}}th{{font-size:.62rem;text-transform:uppercase;color:var(--muted)}}.ticker{{color:var(--accent);font-weight:800}}.num{{text-align:right}}
@media(max-width:1100px){{.app{{grid-template-columns:220px minmax(0,1fr)}}.dashboard{{grid-template-columns:1fr 330px}}}}
@media(max-width:850px){{body{{overflow:auto}}.app{{display:block;height:auto}}.sidebar{{position:relative;height:auto;max-height:420px}}.main{{height:auto;display:block;overflow:visible}}.kpis{{grid-template-columns:1fr 1fr;margin:10px 0}}.dashboard{{display:block}}.card{{margin-bottom:10px}}.chartbox,.corrwrap{{height:280px}}.details{{position:static;margin-top:10px}}}}
</style></head><body><div class="app"><aside class="sidebar"><div class="brand"><div class="eyebrow">Radar prospectif</div><h1>AI Investment Signals</h1><div class="muted">IA · Robotique · Biotech</div></div><input id="search" class="search" placeholder="Rechercher une valeur..."><div class="sidefilters" id="sidefilters"><button class="active" data-theme="all">Tout</button><button data-theme="ai_semi">IA</button><button data-theme="robotics">Robotique</button><button data-theme="biotech_medtech">Biotech</button></div><div id="tickerNav"></div></aside><main class="main">
<div class="topbar"><div class="titleblock"><div class="eyebrow" id="themeLabel">Radar</div><h2><span id="companyName">Sélection</span> <span class="muted" id="tickerLabel"></span></h2><div class="meta"><span id="rolePill" class="pill"></span><span class="pill" id="subthemeLabel"></span><span class="pill" id="lastDate"></span></div></div><div class="muted" style="text-align:right">Dashboard généré<br><b style="color:var(--ink)">{now}</b></div></div>
<div class="kpis"><div class="kpi"><b>{counts['all']}</b><span>Sociétés suivies</span></div><div class="kpi"><b>{counts['anchor']}</b><span>Anchors / blockbusters</span></div><div class="kpi"><b>{counts['enabler']}</b><span>Enablers / emerging</span></div><div class="kpi"><b id="currentPrice">-</b><span>Cours sélectionné</span></div></div>
<div class="dashboard"><section class="card pricecard"><h3>Cotation et Signal Score</h3><div class="chartbox"><canvas id="priceChart"></canvas></div></section><aside class="card scorecard"><div class="signalblock"><h4>Signal Score</h4><div class="scoregrid signalgrid" id="signalGrid"></div></div><h3>Indicateurs de thèse</h3><div class="scoregrid" id="scoreGrid"></div><div class="thesis" id="thesisBox"></div></aside><section class="card corrcard"><h3>Corrélation prospective</h3><div class="controls"><label>Indicateur <select id="indicatorSelect"><option value="industrial_score">Signal industriel</option><option value="financial_score">Confirmation financière</option><option value="criticality_score">Criticité</option><option value="valuation_score">Valorisation</option><option value="evidence_diversity_score">Diversité des preuves</option></select></label><label>Horizon <select id="horizonSelect"><option>M1</option><option>M3</option><option selected>M6</option><option>M12</option></select></label></div><div class="corrwrap"><canvas id="corrChart"></canvas></div><div class="muted" id="corrNote"></div></section><section class="card readcard"><h3>Lecture du dossier</h3><div id="readout" class="muted">Sélectionne une société dans la colonne de gauche.</div></section></div>
<div class="details"><details><summary>Univers complet ({counts['all']})</summary><div class="tablewrap"><table><thead><tr><th>Ticker</th><th>Société</th><th>Thème</th><th>Rôle</th><th>Maillon</th><th>Cours</th><th>Date</th></tr></thead><tbody>{table}</tbody></table></div></details></div></main></div><script>
const ROWS={json.dumps(rows,ensure_ascii=False)},HISTORY={json.dumps(history,ensure_ascii=False)},OUTCOMES={json.dumps(outcomes,ensure_ascii=False)},SIGNAL_HISTORY={json.dumps(signal_history,ensure_ascii=False)};const byTicker=Object.fromEntries(ROWS.map(r=>[r.ticker,r]));let selected=ROWS[0]?.ticker||'',themeFilter='all',priceChart,corrChart;function fmt(v){{return v==null?'-':Number(v).toLocaleString('fr-FR',{{minimumFractionDigits:2,maximumFractionDigits:2}})}}
function buildNav(){{const q=document.getElementById('search').value.toLowerCase(),nav=document.getElementById('tickerNav');nav.innerHTML='';const vis=ROWS.filter(r=>(themeFilter==='all'||r.theme===themeFilter)&&(`${{r.ticker}} ${{r.company}} ${{r.subtheme}}`.toLowerCase().includes(q)));[['anchor','Anchors / blockbusters'],['enabler','Critical enablers'],['emerging','Emerging']].forEach(([role,label])=>{{const items=vis.filter(r=>r.role===role);if(!items.length)return;const h=document.createElement('div');h.className='navgroup';h.textContent=label;nav.appendChild(h);items.forEach(r=>{{const b=document.createElement('button');b.className='tickerbtn'+(r.ticker===selected?' active':'');b.innerHTML=`<b>${{r.ticker}}</b><span>${{fmt(r.close)}}</span><small>${{r.company}} · ${{r.subtheme.replaceAll('_',' ')}}</small>`;b.onclick=()=>selectTicker(r.ticker);nav.appendChild(b)}})}})}}
function selectTicker(t){{selected=t;buildNav();render();document.dispatchEvent(new CustomEvent('ais:tickerchange',{{detail:{{ticker:t}}}}))}}document.getElementById('search').oninput=buildNav;document.querySelectorAll('#sidefilters button').forEach(b=>b.onclick=()=>{{document.querySelectorAll('#sidefilters button').forEach(x=>x.classList.remove('active'));b.classList.add('active');themeFilter=b.dataset.theme;buildNav()}});
function render(){{const r=byTicker[selected];if(!r)return;document.getElementById('companyName').textContent=r.company;document.getElementById('tickerLabel').textContent=`(${{r.ticker}})`;document.getElementById('themeLabel').textContent=r.theme_label;document.getElementById('rolePill').textContent=r.role;document.getElementById('subthemeLabel').textContent=r.subtheme.replaceAll('_',' ');document.getElementById('lastDate').textContent=r.date||'';document.getElementById('currentPrice').textContent=fmt(r.close);const pricePts=HISTORY[r.ticker]||[],signalPts=SIGNAL_HISTORY.filter(x=>x.scores&&x.scores[r.ticker]).map(x=>({{date:x.date,score:x.scores[r.ticker].signal_score}})),labels=[...new Set([...pricePts.map(x=>x.date),...signalPts.map(x=>x.date)])].sort(),priceByDate=Object.fromEntries(pricePts.map(x=>[x.date,x.close])),signalByDate=Object.fromEntries(signalPts.map(x=>[x.date,x.score]));if(priceChart)priceChart.destroy();priceChart=new Chart(document.getElementById('priceChart'),{{type:'line',data:{{labels,datasets:[{{label:`Cours ${{r.ticker}}`,data:labels.map(d=>priceByDate[d]??null),yAxisID:'yPrice',borderColor:'#5fc4cb',backgroundColor:'rgba(95,196,203,.12)',fill:true,tension:.18,pointRadius:0,spanGaps:true}},{{label:'Signal Score /100',data:labels.map(d=>signalByDate[d]??null),yAxisID:'ySignal',borderColor:'#dbb05a',backgroundColor:'#dbb05a',tension:.2,pointRadius:3,spanGaps:true}}]}},options:{{responsive:true,maintainAspectRatio:false,interaction:{{mode:'index',intersect:false}},plugins:{{legend:{{labels:{{color:'#edf3f2',boxWidth:12}}}}}},scales:{{x:{{ticks:{{color:'#91a1a1',maxTicksLimit:6,font:{{size:9}}}},grid:{{color:'#2a383b'}}}},yPrice:{{position:'left',ticks:{{color:'#5fc4cb',font:{{size:9}}}},grid:{{color:'#2a383b'}}}},ySignal:{{position:'right',min:0,max:100,ticks:{{color:'#dbb05a',font:{{size:9}}}},grid:{{drawOnChartArea:false}}}}}}}}}});const s=r.signal_data||{{}},signalMetrics=[['signal_score','Score global /100'],['fundamental_strength','Solidité fondamentale'],['novelty','Nouveauté'],['pricing_headroom','Potentiel non pricé'],['valuation','Valorisation'],['execution_risk','Risque d’exécution (100 = élevé)']];document.getElementById('signalGrid').innerHTML=signalMetrics.map(([k,l])=>`<div class="score"><b>${{s[k]??'-'}}</b><span>${{l}}</span></div>`).join('')+(s.date?`<div class="muted" style="grid-column:1/-1">Snapshot ${{s.date}} · méthode ${{s.method_version}}${{s.signal_score == null ? " · Score incomplet : composantes indisponibles affichées par un tiret." : ""}}</div>`:'<div class="muted" style="grid-column:1/-1">Aucun snapshot disponible.</div>');const t=r.thesis_data||{{}},metrics=[['industrial_score','Signal industriel'],['financial_score','Confirmation financière'],['criticality_score','Criticité'],['valuation_score','Valorisation'],['evidence_diversity_score','Diversité des preuves']];document.getElementById('scoreGrid').innerHTML=metrics.map(([k,l])=>`<div class="score"><b>${{t[k]??'-'}}</b><span>${{l}}</span></div>`).join('');document.getElementById('thesisBox').innerHTML=t.thesis?`<strong>Thèse</strong><p>${{t.thesis}}</p><strong>Catalyseur</strong><p>${{t.catalyst||'-'}}</p><strong>Falsification</strong><p>${{t.falsification||'-'}}</p>`:'<div class="muted">Aucune thèse figée pour cette valeur.</div>';const readout=document.getElementById('readout');if(readout)readout.innerHTML=`<p><b>${{r.company}}</b></p><p class="muted">${{r.theme_label}} · ${{r.role}} · ${{r.subtheme.replaceAll('_',' ')}}</p><p>Cette zone agrégera progressivement preuves, événements, relations clients-fournisseurs, catalyseurs et risques.</p>`}}
function drawCorr(){{const metric=document.getElementById('indicatorSelect').value,h=document.getElementById('horizonSelect').value,pts=OUTCOMES.filter(x=>x.horizon===h&&x[metric]!=null&&x.excess_return!=null).map(x=>({{x:x[metric],y:x.excess_return,ticker:x.ticker}}));if(corrChart)corrChart.destroy();corrChart=new Chart(document.getElementById('corrChart'),{{type:'scatter',data:{{datasets:[{{label:`${{metric}} vs excès ${{h}}`,data:pts,backgroundColor:'#dbb05a',pointRadius:4}}]}},options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{labels:{{color:'#edf3f2',boxWidth:12,font:{{size:9}}}}}}}},scales:{{x:{{ticks:{{color:'#91a1a1',font:{{size:9}}}},grid:{{color:'#2a383b'}}}},y:{{ticks:{{color:'#91a1a1',font:{{size:9}},callback:v=>(v*100)+'%'}},grid:{{color:'#2a383b'}}}}}}}}}});document.getElementById('corrNote').textContent=pts.length<5?'Échantillon insuffisant : aucune conclusion statistique.':'Comparer Pearson et Spearman.'}}document.getElementById('indicatorSelect').onchange=drawCorr;document.getElementById('horizonSelect').onchange=drawCorr;buildNav();render();drawCorr();
</script></body></html>'''
    OUT.write_text(page,encoding='utf-8')

if __name__=='__main__': build()
