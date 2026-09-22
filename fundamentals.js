let AIS_FUND={companies:{}};
const F_METRICS={fcf_per_share:['FCF / action','€/$ par action'],fcf_margin_pct:['Marge FCF','%'],roic_pct:['ROIC','%'],capex_ocf_pct:['CAPEX / OCF','%'],fcf_yield_pct:['FCF yield','%']};
function ffmt(v,s=''){return v==null?'—':Number(v).toLocaleString('fr-FR',{maximumFractionDigits:2})+s}

const SIGNAL_HELP=`
<strong>Lire le Signal Score</strong>
<span>Le score global synthétise cinq dimensions sur 100. Plus haut est favorable, sauf le risque d’exécution où 100 signifie un risque élevé.</span>
<b>Solidité fondamentale</b><span>Qualité de la génération de cash et efficacité du capital, à partir notamment de la marge FCF et du ROIC.</span>
<b>Nouveauté</b><span>Mesure si les informations récentes changent réellement la thèse plutôt que de simplement répéter ce que le marché sait déjà.</span>
<b>Potentiel non pricé</b><span>Évalue la marge entre ce que les nouvelles preuves suggèrent et ce que le cours semble déjà intégrer.</span>
<b>Valorisation</b><span>Met le prix payé en regard de la génération de cash actuelle. Une valorisation favorable ne suffit pas seule à valider une thèse.</span>
<b>Risque d’exécution</b><span>Risque que l’entreprise n’arrive pas à convertir la thèse en résultats. Ici, un score élevé est défavorable.</span>
<span class="ratio-benchmark">Lecture rapide : le score global est un outil de comparaison, pas une règle automatique d’achat.</span>
`;

const THESIS_HELP=`
<strong>Lire les indicateurs de thèse</strong>
<b>Signal industriel</b><span>Traction réelle : demande, backlog, capacité, commandes.</span>
<span class="ratio-benchmark">Repère : &lt;40 faible · 40-60 à confirmer · 60-75 positif · &gt;75 fort</span>
<b>Confirmation financière</b><span>La traction se retrouve dans les revenus, marges et cash-flows.</span>
<span class="ratio-benchmark">Repère : &gt;60 confirme la thèse · &gt;75 confirmation forte</span>
<b>Criticité</b><span>Importance du maillon dans la chaîne de valeur et difficulté à le remplacer.</span>
<span class="ratio-benchmark">Repère : &gt;70 = maillon particulièrement stratégique</span>
<b>Valorisation</b><span>Remet le potentiel en regard du prix payé. À lire avec la croissance et la qualité.</span>
<span class="ratio-benchmark">Repère : &gt;60 favorable · &lt;40 valorisation exigeante</span>
<b>Diversité des preuves</b><span>Plus les sources indépendantes convergent, plus le signal est robuste.</span>
<span class="ratio-benchmark">Repère : &gt;60 correct · &gt;75 robuste</span>
<em>Un tiret signifie qu’aucune thèse figée n’est disponible pour cet indicateur.</em>
`;

const FUND_HELP=`
<strong>Lire les fondamentaux</strong>
<b>FCF yield</b><span>FCF / capitalisation. Mesure le cash libre généré pour le prix payé.</span>
<span class="ratio-benchmark">Repère : &lt;2% exigeant · 2-4% correct si forte croissance · 4-6% attractif · &gt;6% élevé à vérifier</span>
<b>Marge FCF</b><span>FCF / chiffre d’affaires. Mesure la conversion des ventes en cash libre.</span>
<span class="ratio-benchmark">Repère : &lt;10% faible · 10-20% solide · &gt;20% très bon · &gt;30% excellent</span>
<b>ROIC</b><span>Rendement du capital investi. Le point clé est l’écart durable avec le coût du capital.</span>
<span class="ratio-benchmark">Repère : &lt;8% faible · 8-12% correct · 12-20% très bon · &gt;20% excellent</span>
<b>CAPEX / OCF</b><span>Part du cash opérationnel réinvestie. Plus bas n’est pas automatiquement meilleur.</span>
<span class="ratio-benchmark">Repère : &lt;25% léger · 25-50% modéré · &gt;50% très capitalistique ou phase d’investissement</span>
<b>FCF / action</b><span>Cash libre ramené à une action. L’évolution compte davantage que le niveau absolu.</span>
<span class="ratio-benchmark">Repère : pas de cible absolue · viser une progression régulière, idéalement &gt;8-10%/an sur plusieurs années</span>
<b>Croissance FCF</b><span>Tendance pluriannuelle du cash libre. À confronter au FCF yield et à la dilution.</span>
<span class="ratio-benchmark">Repère : 5-10%/an solide · 10-15% fort · &gt;15% très fort si durable</span>
<em>Lecture d’ensemble : qualité + croissance + valorisation. Les seuils sont des ordres de grandeur et varient selon le secteur et la phase d’investissement.</em>
`;

function helpMarkup(label,content){
  return '<span class="ratio-help"><button class="ratio-help-btn" type="button" aria-label="'+label+'" aria-expanded="false">?</button><span class="ratio-tooltip" role="tooltip">'+content+'</span></span>';
}

function setupHelp(sc){
  const positionTip=(btn,tip)=>{
    if(!tip)return;
    const r=sc.getBoundingClientRect(), gap=12, pad=12;
    const w=Math.min(500,Math.max(340,r.left-gap-pad));
    let left=r.left-gap-w;
    if(left<pad) left=pad;
    let top=Math.max(pad,r.top);
    const maxH=Math.max(260,window.innerHeight-top-pad);
    tip.style.setProperty('--ratio-left',`${left}px`);
    tip.style.setProperty('--ratio-top',`${top}px`);
    tip.style.setProperty('--ratio-width',`${w}px`);
    tip.style.setProperty('--ratio-max-height',`${maxH}px`);
  };
  const closeAll=(except=null)=>{
    sc.querySelectorAll('.ratio-help').forEach(wrap=>{
      if(wrap===except)return;
      wrap.classList.remove('open');
      wrap.querySelector('.ratio-help-btn')?.setAttribute('aria-expanded','false');
    });
  };
  sc.querySelectorAll('.ratio-help-btn').forEach(btn=>{
    const tip=btn.nextElementSibling;
    btn.addEventListener('mouseenter',()=>positionTip(btn,tip));
    btn.addEventListener('focus',()=>positionTip(btn,tip));
    btn.addEventListener('click',e=>{
      e.stopPropagation();
      positionTip(btn,tip);
      const wrap=btn.closest('.ratio-help');
      const willOpen=!wrap.classList.contains('open');
      closeAll(wrap);
      wrap.classList.toggle('open',willOpen);
      btn.setAttribute('aria-expanded',String(willOpen));
    });
  });
  window.addEventListener('resize',()=>sc.querySelectorAll('.ratio-help.open .ratio-help-btn').forEach(btn=>positionTip(btn,btn.nextElementSibling)));
  document.addEventListener('click',()=>closeAll());
}

function addFundUI(){
 const pc=document.querySelector('.pricecard h3'); if(pc&&!document.getElementById('fundMetric')) pc.innerHTML='Cotation & fondamentaux <select id="fundMetric" style="float:right"><option value="">Cours seul</option>'+Object.entries(F_METRICS).map(([k,v])=>`<option value="${k}">${v[0]}</option>`).join('')+'</select>';
 const sc=document.querySelector('.scorecard');
 if(sc&&!document.getElementById('fundCards')){
   sc.classList.add('with-fundamentals');

   const signalHeading=sc.querySelector('.signalblock h4');
   if(signalHeading) signalHeading.innerHTML='Signal Score '+helpMarkup('Comment lire le Signal Score',SIGNAL_HELP);

   const thesisHeading=sc.querySelector('h3');
   if(thesisHeading) thesisHeading.innerHTML='Indicateurs de thèse '+helpMarkup('Comment lire les indicateurs de thèse',THESIS_HELP);

   sc.insertAdjacentHTML('beforeend','<div class="fund-section-title"><span>Fondamentaux</span>'+helpMarkup('Comment lire les fondamentaux',FUND_HELP)+'</div><div id="fundCards" class="scoregrid fund-grid"></div>');
   setupHelp(sc);
 }
 if(!document.getElementById('fundCompactStyle')){
   const style=document.createElement('style'); style.id='fundCompactStyle'; style.textContent=`
   .scorecard.with-fundamentals{display:flex;flex-direction:column;gap:5px;overflow:auto;position:relative}
   .scorecard.with-fundamentals>h3{margin-bottom:2px;display:flex;align-items:center;justify-content:space-between;gap:8px}
   .scorecard.with-fundamentals>.scoregrid{grid-template-columns:repeat(3,minmax(0,1fr));gap:5px}
   .scorecard.with-fundamentals .score{padding:6px 7px;min-height:47px;display:flex;flex-direction:column;justify-content:center;min-width:0}
   .scorecard.with-fundamentals .score b{font-size:.98rem;line-height:1.08;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
   .scorecard.with-fundamentals .score span{font-size:.59rem;line-height:1.15;margin-top:4px;white-space:normal}
   .scorecard.with-fundamentals .thesis{margin-top:1px;padding-top:5px;flex:0 0 auto}
   .signalblock h4{display:flex;align-items:center;justify-content:space-between;gap:8px}
   .fund-section-title{margin-top:1px;padding-top:5px;border-top:1px solid var(--rule);font-size:.68rem;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);font-weight:800;display:flex;align-items:center;justify-content:space-between;gap:8px}
   .scorecard.with-fundamentals .fund-grid{margin-top:0!important}
   .ratio-help{position:relative;display:inline-flex;flex:0 0 auto}
   .ratio-help-btn{width:22px;height:22px;padding:0;border-radius:50%;display:grid;place-items:center;background:var(--panel2);border:1px solid var(--accent);color:var(--accent);font-size:.78rem;font-weight:900;line-height:1}
   .ratio-help-btn:hover,.ratio-help.open .ratio-help-btn{background:var(--accent);color:var(--bg)}
   .ratio-tooltip{display:none;position:fixed;z-index:80;left:var(--ratio-left,12px);top:var(--ratio-top,12px);width:var(--ratio-width,500px);max-height:var(--ratio-max-height,76vh);overflow:auto;padding:18px 19px;background:#101719;border:1px solid var(--accent);border-radius:10px;box-shadow:0 14px 36px rgba(0,0,0,.48);color:#d4dddc;font-size:.94rem;line-height:1.58;font-weight:400;text-align:left;text-transform:none;letter-spacing:normal}
   .ratio-help:hover .ratio-tooltip,.ratio-help:focus-within .ratio-tooltip,.ratio-help.open .ratio-tooltip{display:grid;grid-template-columns:1fr;gap:5px}
   .ratio-tooltip strong{font-size:1.12rem;line-height:1.3;color:var(--ink);margin-bottom:7px}
   .ratio-tooltip b{color:var(--accent);font-size:.96rem;line-height:1.35;margin-top:8px}
   .ratio-tooltip .ratio-benchmark{color:#e4bd68;font-size:.88rem;line-height:1.45;font-weight:700;margin:1px 0 4px}
   .ratio-tooltip em{margin-top:11px;padding:10px 11px;border-radius:7px;background:var(--panel2);color:var(--ink);font-size:.88rem;line-height:1.5;font-style:normal;font-weight:700}

   .readcard h3{font-size:1.02rem!important;margin-bottom:10px!important}
   .readcard .brief-memory-scroll{overflow:auto;max-height:100%}
   .readcard .brief-memory-item{border-left:2px solid var(--accent);padding:1px 0 12px 12px;margin-bottom:14px}
   .readcard .brief-memory-title{font-size:.88rem;color:var(--accent);font-weight:800;line-height:1.35}
   .readcard .brief-memory-summary{font-size:.9rem;color:#d4dddc;margin-top:6px;line-height:1.55}
   .readcard .brief-memory-watch{font-size:.8rem;margin-top:6px;line-height:1.48}
   /* Fallback for the currently generated index until the next scheduled rebuild. */
   .readcard>div>div[style*="border-left"]{padding:1px 0 12px 12px!important;margin-bottom:14px!important}
   .readcard>div>div[style*="border-left"]>div:first-child{font-size:.88rem!important;line-height:1.35!important}
   .readcard>div>div[style*="border-left"]>div:nth-child(2){font-size:.9rem!important;line-height:1.55!important;margin-top:6px!important}
   .readcard>div>div[style*="border-left"]>div:nth-child(3){font-size:.8rem!important;line-height:1.48!important;margin-top:6px!important}

   .readcard{cursor:pointer;position:relative}
   .readcard:hover{border-color:rgba(95,196,203,.58)}
   .readcard h3{display:flex;align-items:center;justify-content:space-between;gap:10px}
   .brief-open-hint{display:inline-flex;align-items:center;gap:5px;color:var(--accent);font-size:.7rem;font-weight:800;white-space:nowrap}
   .brief-open-hint::before{content:'↗';font-size:.82rem}

   body.brief-archive-open{overflow:hidden}
   .brief-archive-overlay{display:none;position:fixed;inset:0;z-index:140;background:rgba(3,8,10,.82);backdrop-filter:blur(5px);padding:4vh 3vw}
   .brief-archive-overlay.open{display:flex;align-items:center;justify-content:center}
   .brief-archive-modal{width:min(1180px,94vw);height:min(88vh,920px);display:flex;flex-direction:column;background:#101719;border:1px solid var(--accent);border-radius:14px;box-shadow:0 24px 70px rgba(0,0,0,.6);overflow:hidden}
   .brief-archive-head{display:flex;justify-content:space-between;align-items:flex-start;gap:20px;padding:20px 22px 14px;border-bottom:1px solid var(--rule)}
   .brief-archive-head h2{margin:0;font-size:1.4rem}
   .brief-archive-subtitle{margin-top:4px;color:var(--muted);font-size:.88rem}
   .brief-archive-close{width:34px;height:34px;padding:0;border-radius:50%;font-size:1.15rem;line-height:1;background:var(--panel2);border:1px solid var(--rule)}
   .brief-archive-close:hover{border-color:var(--accent);color:var(--accent)}
   .brief-archive-tools{display:grid;grid-template-columns:minmax(260px,1.5fr) minmax(150px,.55fr) minmax(150px,.55fr) auto;gap:10px;align-items:end;padding:14px 22px;border-bottom:1px solid var(--rule);background:rgba(18,28,30,.75)}
   .brief-archive-field{display:flex;flex-direction:column;gap:5px}
   .brief-archive-field label{font-size:.72rem;color:var(--muted);font-weight:800;text-transform:uppercase;letter-spacing:.06em}
   .brief-archive-field input{width:100%;background:var(--panel2);border:1px solid var(--rule);border-radius:8px;color:var(--ink);padding:9px 10px;font:inherit}
   .brief-archive-field input:focus{outline:none;border-color:var(--accent)}
   .brief-archive-reset{border-radius:8px;height:38px;padding:0 12px}
   .brief-archive-meta{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:10px 22px;color:var(--muted);font-size:.8rem;border-bottom:1px solid var(--rule)}
   .brief-archive-list{overflow:auto;padding:4px 22px 22px}
   .brief-archive-item{padding:18px 4px 18px 14px;border-left:3px solid var(--accent);border-bottom:1px solid var(--rule)}
   .brief-archive-item:last-child{border-bottom:0}
   .brief-archive-date{color:var(--accent);font-size:.9rem;font-weight:900}
   .brief-archive-stance{color:var(--amber);font-weight:800}
   .brief-archive-summary{margin-top:8px;color:#e0e8e7;font-size:1rem;line-height:1.65}
   .brief-archive-watch{margin-top:9px;color:var(--muted);font-size:.9rem;line-height:1.55}
   .brief-archive-watch b{color:#b9c8c7}
   .brief-archive-tickers{margin-top:8px;display:flex;gap:5px;flex-wrap:wrap}
   .brief-archive-ticker{font-size:.68rem;border:1px solid var(--rule);border-radius:999px;padding:2px 7px;color:var(--accent)}
   .brief-archive-empty{padding:42px 10px;text-align:center;color:var(--muted);font-size:.95rem}

   @media(max-width:1100px){.scorecard.with-fundamentals>.scoregrid{grid-template-columns:repeat(2,minmax(0,1fr))}.scorecard.with-fundamentals .score{min-height:43px;padding:5px 6px}.scorecard.with-fundamentals .score b{font-size:.9rem}.brief-archive-tools{grid-template-columns:1fr 1fr}.brief-archive-search{grid-column:1/-1}}
   @media(max-width:850px){.scorecard.with-fundamentals{overflow:visible}.scorecard.with-fundamentals>.scoregrid{grid-template-columns:repeat(2,minmax(0,1fr))}.ratio-tooltip{left:16px!important;right:16px;top:16px!important;width:auto!important;max-height:80vh!important;font-size:.96rem}.ratio-tooltip strong{font-size:1.1rem}.readcard .brief-memory-summary{font-size:.94rem}}
   `; document.head.appendChild(style);
 }
 document.getElementById('fundMetric')?.addEventListener('change',renderFundamentals);
}
function renderFundamentals(){
 const c=AIS_FUND.companies?.[selected];
 const box=document.getElementById('fundCards');
 if(!c){if(box)box.innerHTML='<div class="muted">Fondamentaux indisponibles pour cette valeur.</div>';return;}
 const l=c.latest||{}, cards=[['FCF yield',l.fcf_yield_pct,'%'],['Marge FCF',l.fcf_margin_pct,'%'],['ROIC',l.roic_pct,'%'],['CAPEX / OCF',l.capex_ocf_pct,'%'],['FCF/action',l.fcf_per_share,''],['Croissance FCF',l.fcf_cagr_available_pct,'%']];
 if(box) box.innerHTML=cards.map(x=>`<div class="score"><b title="${ffmt(x[1],x[2])}">${ffmt(x[1],x[2])}</b><span>${x[0]}</span></div>`).join('');
 if(!priceChart)return; priceChart.data.datasets=priceChart.data.datasets.filter(d=>d.aisFund!==true); delete priceChart.options.scales.y1;
 const key=document.getElementById('fundMetric')?.value; if(key&&c.annual?.length){
   const map=new Map(c.annual.filter(x=>x[key]!=null).map(x=>[String(x.year),x[key]]));
   const vals=priceChart.data.labels.map(d=>map.get(String(d).slice(0,4))??null);
   priceChart.data.datasets.push({label:F_METRICS[key][0],data:vals,borderColor:'#dbb05a',backgroundColor:'transparent',pointRadius:2,spanGaps:true,yAxisID:'y1',aisFund:true});
   priceChart.options.scales.y1={position:'right',ticks:{color:'#dbb05a',font:{size:9}},grid:{drawOnChartArea:false}};
 }
 priceChart.update();
}

let AIS_BRIEF_ARCHIVE=[];

function briefEscapeHtml(value){
  return String(value==null?'':value).replace(/[&<>"']/g,function(ch){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]});
}
function briefSearchText(item){
  return [item.date,item.stance,item.summary,item.watch_next].concat(item.tickers||[]).filter(Boolean).join(' ').toLowerCase();
}
function renderBriefArchive(){
  const list=document.getElementById('briefArchiveList');
  const meta=document.getElementById('briefArchiveCount');
  if(!list||!meta)return;
  const q=(document.getElementById('briefArchiveSearch')?.value||'').trim().toLowerCase();
  const from=document.getElementById('briefArchiveFrom')?.value||'';
  const to=document.getElementById('briefArchiveTo')?.value||'';
  const filtered=[...AIS_BRIEF_ARCHIVE]
    .filter(function(item){return (!q||briefSearchText(item).includes(q))&&(!from||String(item.date||'')>=from)&&(!to||String(item.date||'')<=to)})
    .sort(function(a,b){return String(b.date||'').localeCompare(String(a.date||''))});
  meta.textContent=String(filtered.length)+' brief'+(filtered.length>1?'s':'')+' affiché'+(filtered.length>1?'s':'')+' sur '+String(AIS_BRIEF_ARCHIVE.length);
  if(!filtered.length){
    list.innerHTML='<div class="brief-archive-empty">Aucun brief ne correspond à ces filtres.</div>';
    return;
  }
  list.innerHTML=filtered.map(function(item){
    const stance=item.stance?' · <span class="brief-archive-stance">'+briefEscapeHtml(item.stance)+'</span>':'';
    const watch=item.watch_next?'<div class="brief-archive-watch"><b>À surveiller :</b> '+briefEscapeHtml(item.watch_next)+'</div>':'';
    const tickers=(item.tickers||[]).length?'<div class="brief-archive-tickers">'+item.tickers.map(function(t){return '<span class="brief-archive-ticker">'+briefEscapeHtml(t)+'</span>'}).join('')+'</div>':'';
    return '<article class="brief-archive-item"><div class="brief-archive-date">'+briefEscapeHtml(item.date||'')+stance+'</div><div class="brief-archive-summary">'+briefEscapeHtml(item.summary||'')+'</div>'+watch+tickers+'</article>';
  }).join('');
}
function openBriefArchive(){
  const overlay=document.getElementById('briefArchiveOverlay');
  if(!overlay)return;
  overlay.classList.add('open');
  overlay.setAttribute('aria-hidden','false');
  document.body.classList.add('brief-archive-open');
  renderBriefArchive();
  setTimeout(function(){document.getElementById('briefArchiveSearch')?.focus()},30);
}
function closeBriefArchive(){
  const overlay=document.getElementById('briefArchiveOverlay');
  if(!overlay)return;
  overlay.classList.remove('open');
  overlay.setAttribute('aria-hidden','true');
  document.body.classList.remove('brief-archive-open');
}
function setupBriefArchive(){
  const card=document.querySelector('.readcard');
  if(!card||document.getElementById('briefArchiveOverlay'))return;
  card.setAttribute('role','button');
  card.setAttribute('tabindex','0');
  card.setAttribute('aria-label','Ouvrir les archives des briefs');
  const title=card.querySelector('h3');
  if(title&&!title.querySelector('.brief-open-hint')) title.insertAdjacentHTML('beforeend','<span class="brief-open-hint">Ouvrir l’archive</span>');
  card.addEventListener('click',openBriefArchive);
  card.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();openBriefArchive()}});

  const modalHtml=
    '<div class="brief-archive-overlay" id="briefArchiveOverlay" aria-hidden="true">'+
      '<section class="brief-archive-modal" role="dialog" aria-modal="true" aria-labelledby="briefArchiveTitle">'+
        '<header class="brief-archive-head">'+
          '<div><h2 id="briefArchiveTitle">Mémoire des briefs</h2><div class="brief-archive-subtitle">Archive chronologique, recherche plein texte et filtrage par dates</div></div>'+
          '<button class="brief-archive-close" id="briefArchiveClose" type="button" aria-label="Fermer">×</button>'+
        '</header>'+
        '<div class="brief-archive-tools">'+
          '<div class="brief-archive-field brief-archive-search"><label for="briefArchiveSearch">Recherche</label><input id="briefArchiveSearch" type="search" placeholder="Ex. HBM, robotique, valorisation, QCOM..."></div>'+
          '<div class="brief-archive-field"><label for="briefArchiveFrom">Du</label><input id="briefArchiveFrom" type="date"></div>'+
          '<div class="brief-archive-field"><label for="briefArchiveTo">Au</label><input id="briefArchiveTo" type="date"></div>'+
          '<button class="brief-archive-reset" id="briefArchiveReset" type="button">Réinitialiser</button>'+
        '</div>'+
        '<div class="brief-archive-meta"><span id="briefArchiveCount"></span><span>Tri : plus récent d’abord</span></div>'+
        '<div class="brief-archive-list" id="briefArchiveList"></div>'+
      '</section>'+
    '</div>';
  document.body.insertAdjacentHTML('beforeend',modalHtml);

  ['briefArchiveSearch','briefArchiveFrom','briefArchiveTo'].forEach(function(id){document.getElementById(id)?.addEventListener('input',renderBriefArchive)});
  document.getElementById('briefArchiveReset')?.addEventListener('click',function(){
    ['briefArchiveSearch','briefArchiveFrom','briefArchiveTo'].forEach(function(id){const el=document.getElementById(id);if(el)el.value=''});
    renderBriefArchive();
  });
  document.getElementById('briefArchiveClose')?.addEventListener('click',function(e){e.stopPropagation();closeBriefArchive()});
  document.getElementById('briefArchiveOverlay')?.addEventListener('click',function(e){if(e.target===e.currentTarget)closeBriefArchive()});
  document.addEventListener('keydown',function(e){if(e.key==='Escape')closeBriefArchive()});
}

fetch('/data/brief_memory.json').then(function(r){return r.ok?r.json():[]}).then(function(d){
  AIS_BRIEF_ARCHIVE=Array.isArray(d)?d:[];
  setupBriefArchive();
  renderBriefArchive();
}).catch(function(){AIS_BRIEF_ARCHIVE=[];setupBriefArchive();renderBriefArchive()});

fetch('/data/fundamentals.json').then(r=>r.ok?r.json():{companies:{}}).then(d=>{AIS_FUND=d;addFundUI();renderFundamentals();setupBriefArchive()}).catch(()=>{setupBriefArchive()});
document.addEventListener('ais:tickerchange',renderFundamentals);
