(() => {
  const ACCENT='#5fc4cb', GREEN='#6fc08d', AMBER='#dbb05a', MUTED='#91a1a1', RULE='#2a383b';
  let cfg=null, bench=null, portfolioChart=null;
  const money=v=>Number(v||0).toLocaleString('fr-FR',{style:'currency',currency:(cfg&&cfg.currency)||'USD',maximumFractionDigits:0});
  const pct=v=>(Number(v||0)*100).toLocaleString('fr-FR',{minimumFractionDigits:2,maximumFractionDigits:2})+' %';
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  function installStyle(){
    if(document.getElementById('portfolioStyle')) return;
    const s=document.createElement('style'); s.id='portfolioStyle'; s.textContent=`
      .mode-tabs{display:flex;gap:5px;margin-top:9px}.mode-tab{font-size:.68rem;padding:5px 8px}.main.portfolio-active{display:block;overflow:auto}.main.portfolio-active>:not(.portfolio-view){display:none!important}
      body.portfolio-mode .sidebar>.search,body.portfolio-mode .sidebar>.sidefilters,body.portfolio-mode #tickerNav{display:none!important}
      .portfolio-view{min-height:100%;padding-bottom:18px}.pf-head{display:flex;justify-content:space-between;gap:16px;align-items:flex-start;border-bottom:1px solid var(--rule);padding-bottom:9px;margin-bottom:10px}.pf-head h2{font-size:clamp(1.7rem,2.8vw,2.5rem);margin:2px 0 4px}.pf-badge{display:inline-block;border:1px solid var(--rule);border-radius:999px;padding:3px 7px;font-size:.64rem;color:var(--muted)}
      .pf-kpis{display:grid;grid-template-columns:repeat(5,minmax(115px,1fr));gap:7px;margin-bottom:10px}.pf-kpi{background:var(--panel);border:1px solid var(--rule);border-radius:10px;padding:9px 11px}.pf-kpi b{display:block;font-size:1.16rem}.pf-kpi span{font-size:.66rem;color:var(--muted)}.pf-positive{color:var(--green)!important}.pf-negative{color:#e58b8b!important}
      .pf-grid{display:grid;grid-template-columns:minmax(0,1.6fr) minmax(300px,.7fr);gap:10px}.pf-card{background:var(--panel);border:1px solid var(--rule);border-radius:10px;padding:11px;min-width:0}.pf-card h3{font-size:.88rem;margin:0 0 8px}.pf-chart{height:310px;position:relative}.pf-rules{display:grid;grid-template-columns:1fr 1fr;gap:6px}.pf-rule{background:var(--panel2);border:1px solid var(--rule);border-radius:8px;padding:8px}.pf-rule b{display:block;font-size:.88rem}.pf-rule span{font-size:.65rem;color:var(--muted)}
      .pf-wide{grid-column:1/-1}.pf-table{width:100%;min-width:820px}.pf-tablewrap{overflow:auto;max-height:270px}.pf-empty{border:1px dashed var(--rule);border-radius:8px;padding:18px;text-align:center;color:var(--muted)}.pf-note{margin-top:8px;padding:8px;border-left:2px solid var(--accent);background:rgba(95,196,203,.05);font-size:.7rem;color:#cad4d3}.pf-method{font-size:.66rem;color:var(--muted);margin-top:6px}.pf-journal{display:grid;gap:6px}.pf-entry{background:var(--panel2);border:1px solid var(--rule);border-radius:8px;padding:8px}.pf-entry strong{color:var(--accent)}
      @media(max-width:1100px){.pf-kpis{grid-template-columns:repeat(3,1fr)}.pf-grid{grid-template-columns:1fr 330px}}
      @media(max-width:850px){.pf-kpis{grid-template-columns:1fr 1fr}.pf-grid{display:block}.pf-card{margin-bottom:10px}.pf-chart{height:280px}}
    `; document.head.appendChild(s);
  }

  function installTabs(){
    const brand=document.querySelector('.brand'); if(!brand||document.getElementById('modeTabs')) return;
    const tabs=document.createElement('div'); tabs.id='modeTabs'; tabs.className='mode-tabs';
    tabs.innerHTML='<button class="mode-tab active" data-mode="radar">Radar</button><button class="mode-tab" data-mode="portfolio">Portefeuille virtuel</button>';
    brand.appendChild(tabs);
    tabs.querySelector('[data-mode="radar"]').onclick=showRadar;
    tabs.querySelector('[data-mode="portfolio"]').onclick=showPortfolio;
  }

  function setActive(mode){document.querySelectorAll('.mode-tab').forEach(b=>b.classList.toggle('active',b.dataset.mode===mode));}
  function showRadar(){setActive('radar');document.body.classList.remove('portfolio-mode');const main=document.querySelector('.main');main.classList.remove('portfolio-active');window.dispatchEvent(new Event('resize'));}
  async function showPortfolio(){
    setActive('portfolio');document.body.classList.add('portfolio-mode');const main=document.querySelector('.main');main.classList.add('portfolio-active');
    let view=main.querySelector('.portfolio-view');if(!view){view=document.createElement('div');view.className='portfolio-view';main.appendChild(view);}view.innerHTML='<div class="pf-empty">Chargement du portefeuille versionné…</div>';
    try{
      if(!cfg)cfg=await fetch('/data/portfolio.json?ts='+Date.now()).then(r=>{if(!r.ok)throw new Error('portfolio.json');return r.json()});
      const raw=(typeof HISTORY!=='undefined'&&HISTORY[cfg.benchmark.ticker])||[];
      bench={prices:raw.map(p=>({date:p.date,value:p.close}))};
      renderPortfolio(view);
    }catch(e){view.innerHTML='<div class="pf-empty">Impossible de charger le portefeuille versionné.</div>';}
  }

  function latestPrice(ticker){const r=(typeof ROWS!=='undefined'?ROWS:[]).find(x=>x.ticker===ticker);if(r&&r.close!=null)return Number(r.close);const h=(typeof HISTORY!=='undefined'&&HISTORY[ticker])||[];return h.length?Number(h[h.length-1].close):null;}
  function holdingsNow(){const h={},txs=[...(cfg.transactions||[])].sort((a,b)=>a.date.localeCompare(b.date));let cash=Number(cfg.initial_capital);txs.forEach(t=>{const q=Number(t.quantity),p=Number(t.price),fees=Number(t.fees||0),sign=t.side==='sell'?-1:1;h[t.ticker]=(h[t.ticker]||0)+sign*q;cash+=t.side==='sell'?q*p-fees:-(q*p+fees);});const positions=Object.entries(h).filter(([,q])=>q>1e-10).map(([ticker,quantity])=>{const price=latestPrice(ticker);return {ticker,quantity,price,value:price==null?0:quantity*price};});return {cash,positions,value:cash+positions.reduce((s,p)=>s+p.value,0)};}
  function allDates(){const dates=new Set(),inception=cfg.inception_date;Object.values(typeof HISTORY!=='undefined'?HISTORY:{}).forEach(arr=>arr.forEach(p=>{if(p.date>=inception)dates.add(p.date)}));(cfg.transactions||[]).forEach(t=>dates.add(t.date));return [...dates].sort();}
  function priceAt(ticker,date){const arr=(typeof HISTORY!=='undefined'&&HISTORY[ticker])||[];let v=null;for(const p of arr){if(p.date<=date)v=Number(p.close);else break;}return v;}
  function portfolioValueAt(date){const pos={};let cash=Number(cfg.initial_capital);[...(cfg.transactions||[])].sort((a,b)=>a.date.localeCompare(b.date)).forEach(t=>{if(t.date>date)return;const q=Number(t.quantity),p=Number(t.price),fees=Number(t.fees||0),sgn=t.side==='sell'?-1:1;pos[t.ticker]=(pos[t.ticker]||0)+sgn*q;cash+=t.side==='sell'?q*p-fees:-(q*p+fees);});let value=cash;Object.entries(pos).forEach(([ticker,q])=>{if(q<=0)return;const p=priceAt(ticker,date);if(p!=null)value+=q*p;else{const tx=[...(cfg.transactions||[])].reverse().find(t=>t.ticker===ticker&&t.date<=date);if(tx)value+=q*Number(tx.price);}});return value;}
  function universeIndex(date){const vals=[];for(const ticker of cfg.universe_snapshot||[]){const arr=((typeof HISTORY!=='undefined'&&HISTORY[ticker])||[]).filter(p=>p.date>=cfg.inception_date&&p.date<=date);if(!arr.length)continue;const base=Number(arr[0].close),last=Number(arr[arr.length-1].close);if(base>0)vals.push(last/base);}return vals.length?100*vals.reduce((a,b)=>a+b,0)/vals.length:null;}
  function benchmarkIndex(date){const arr=(bench&&bench.prices||[]).filter(p=>p.date>=cfg.inception_date&&p.date<=date);if(!arr.length)return null;return 100*Number(arr[arr.length-1].value)/Number(arr[0].value);}
  function maxDrawdown(series){let peak=-Infinity,dd=0;series.forEach(v=>{if(v>peak)peak=v;if(peak>0)dd=Math.min(dd,v/peak-1)});return dd;}
  function sharpe(series){if(series.length<20)return null;const r=[];for(let i=1;i<series.length;i++)if(series[i-1]>0)r.push(series[i]/series[i-1]-1);if(r.length<10)return null;const m=r.reduce((a,b)=>a+b,0)/r.length,sd=Math.sqrt(r.reduce((s,x)=>s+(x-m)**2,0)/(r.length-1));return sd?m/sd*Math.sqrt(252):null;}

  function renderPortfolio(view){
    const now=holdingsNow(),perf=now.value/Number(cfg.initial_capital)-1,bp=(bench&&bench.prices||[]).filter(p=>p.date>=cfg.inception_date),bperf=bp.length>1?Number(bp[bp.length-1].value)/Number(bp[0].value)-1:0,alpha=perf-bperf;
    const dates=allDates(),aisValues=dates.map(portfolioValueAt),aisIndex=aisValues.map(v=>100*v/Number(cfg.initial_capital)),uni=dates.map(universeIndex),bi=dates.map(benchmarkIndex),dd=maxDrawdown(aisValues),sh=sharpe(aisValues),invested=now.positions.reduce((s,p)=>s+p.value,0),cashPct=now.value?now.cash/now.value:1;
    const positions=now.positions.map(p=>{const txs=(cfg.transactions||[]).filter(t=>t.ticker===p.ticker&&t.side==='buy'),cost=txs.reduce((s,t)=>s+Number(t.quantity)*Number(t.price)+Number(t.fees||0),0),qty=txs.reduce((s,t)=>s+Number(t.quantity),0),pru=qty?cost/qty:null,ret=pru&&p.price?p.price/pru-1:null;return {...p,pru,ret,weight:now.value?p.value/now.value:0};});
    const txRows=(cfg.transactions||[]).slice().reverse().map(t=>`<div class="pf-entry"><strong>${esc(t.date)} · ${esc((t.side||'buy').toUpperCase())} ${esc(t.ticker)}</strong> · ${esc(t.quantity)} @ ${esc(t.price)}<br><span class="muted">${esc(t.reason||'Motif non renseigné')}</span></div>`).join('');
    view.innerHTML=`<div class="pf-head"><div><div class="eyebrow">Expérience prospective</div><h2>Portefeuille virtuel AIS</h2><div class="muted">Objectif : vérifier si nos décisions battent durablement un MSCI World sans réécrire l'histoire.</div></div><div style="text-align:right"><span class="pf-badge">Départ ${esc(cfg.inception_date)}</span><br><span class="pf-badge" style="margin-top:5px">Capital ${money(cfg.initial_capital)}</span></div></div>
    <div class="pf-kpis"><div class="pf-kpi"><b>${money(now.value)}</b><span>Valeur AIS</span></div><div class="pf-kpi"><b class="${perf>=0?'pf-positive':'pf-negative'}">${pct(perf)}</b><span>Performance AIS</span></div><div class="pf-kpi"><b>${pct(bperf)}</b><span>MSCI World</span></div><div class="pf-kpi"><b class="${alpha>=0?'pf-positive':'pf-negative'}">${alpha>=0?'+':''}${pct(alpha)}</b><span>Alpha vs World</span></div><div class="pf-kpi"><b>${pct(cashPct)}</b><span>Cash</span></div></div>
    <div class="pf-grid"><section class="pf-card"><h3>100 investis depuis le départ</h3><div class="pf-chart"><canvas id="portfolioChart"></canvas></div><div class="pf-method">AIS = portefeuille réellement décidé · World = ${esc(cfg.benchmark.label)} · Univers = snapshot équipondéré des ${cfg.universe_snapshot.length} valeurs suivies au lancement.</div></section>
    <aside class="pf-card"><h3>Discipline du test</h3><div class="pf-rules"><div class="pf-rule"><b>${cfg.rules.normal_position_pct}%</b><span>Position normale</span></div><div class="pf-rule"><b>${cfg.rules.max_position_pct_at_entry}% max</b><span>Par valeur à l'entrée</span></div><div class="pf-rule"><b>${cfg.rules.max_positions}</b><span>Positions maximum</span></div><div class="pf-rule"><b>${cfg.rules.max_theme_pct_at_entry}% max</b><span>Par thème à l'entrée</span></div><div class="pf-rule"><b>${pct(dd)}</b><span>Max drawdown AIS</span></div><div class="pf-rule"><b>${sh==null?'—':sh.toLocaleString('fr-FR',{maximumFractionDigits:2})}</b><span>Sharpe annualisé</span></div></div><div class="pf-note">Aucun stop-loss mécanique. Une vente doit être justifiée par rupture de thèse, valorisation extrême, meilleure opportunité ou limite de risque.</div></aside>
    <section class="pf-card pf-wide"><h3>Positions actuelles</h3>${positions.length?`<div class="pf-tablewrap"><table class="pf-table"><thead><tr><th>Valeur</th><th>Quantité</th><th>PRU</th><th>Cours</th><th>Valeur</th><th>Poids</th><th>Perf.</th></tr></thead><tbody>${positions.map(p=>`<tr><td class="ticker">${esc(p.ticker)}</td><td>${p.quantity.toLocaleString('fr-FR',{maximumFractionDigits:4})}</td><td>${p.pru==null?'—':money(p.pru)}</td><td>${p.price==null?'—':money(p.price)}</td><td>${money(p.value)}</td><td>${pct(p.weight)}</td><td class="${p.ret>=0?'pf-positive':'pf-negative'}">${p.ret==null?'—':pct(p.ret)}</td></tr>`).join('')}</tbody></table></div>`:`<div class="pf-empty"><b>Portefeuille volontairement vide au lancement.</b><br>La première ligne sera créée uniquement lorsqu'un signal prospectif justifiera réellement un achat. Le cash fait partie du test.</div>`}</section>
    <section class="pf-card"><h3>Journal immuable des décisions</h3><div class="pf-journal">${txRows||'<div class="pf-empty">Aucune transaction figée. Chaque futur achat conservera son prix, son motif et le snapshot des indicateurs du jour.</div>'}</div></section>
    <aside class="pf-card"><h3>Lecture expérimentale</h3><div class="pf-rule"><b>${money(invested)}</b><span>Capital actuellement investi</span></div><div class="pf-note">Le troisième témoin est essentiel : si AIS bat le World mais pas l'univers équipondéré, le thème était bon mais notre sélection n'a pas créé d'alpha. Si AIS bat les deux, le stock-picking apporte réellement quelque chose.</div></aside></div>`;
    drawPortfolioChart(dates,aisIndex,bi,uni);
  }

  function drawPortfolioChart(labels,ais,world,universe){if(portfolioChart)portfolioChart.destroy();const c=document.getElementById('portfolioChart');if(!c)return;portfolioChart=new Chart(c,{type:'line',data:{labels,datasets:[{label:'AIS Portfolio',data:ais,borderColor:ACCENT,backgroundColor:'transparent',tension:.18,pointRadius:0,borderWidth:2},{label:'MSCI World',data:world,borderColor:GREEN,backgroundColor:'transparent',tension:.18,pointRadius:0,borderWidth:2},{label:'Univers AIS équipondéré',data:universe,borderColor:AMBER,backgroundColor:'transparent',tension:.18,pointRadius:0,borderWidth:1.5}]},options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},plugins:{legend:{labels:{color:'#edf3f2',boxWidth:12}}},scales:{x:{ticks:{color:MUTED,maxTicksLimit:8,font:{size:9}},grid:{color:RULE}},y:{ticks:{color:MUTED,font:{size:9},callback:v=>Number(v).toFixed(0)},grid:{color:RULE}}}}});}

  installStyle();installTabs();
})();
