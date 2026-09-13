let AIS_FUND={companies:{}};
const F_METRICS={fcf_per_share:['FCF / action','€/$ par action'],fcf_margin_pct:['Marge FCF','%'],roic_pct:['ROIC','%'],capex_ocf_pct:['CAPEX / OCF','%'],fcf_yield_pct:['FCF yield','%']};
function ffmt(v,s=''){return v==null?'—':Number(v).toLocaleString('fr-FR',{maximumFractionDigits:2})+s}
function addFundUI(){
 const pc=document.querySelector('.pricecard h3'); if(pc&&!document.getElementById('fundMetric')) pc.innerHTML='Cotation & fondamentaux <select id="fundMetric" style="float:right"><option value="">Cours seul</option>'+Object.entries(F_METRICS).map(([k,v])=>`<option value="${k}">${v[0]}</option>`).join('')+'</select>';
 const sc=document.querySelector('.scorecard');
 if(sc&&!document.getElementById('fundCards')){
   sc.classList.add('with-fundamentals');
   const h=sc.querySelector('h3');
   if(h) h.innerHTML='Indicateurs de thèse <span class="ratio-help"><button class="ratio-help-btn" type="button" aria-label="Comment lire les indicateurs" aria-expanded="false">?</button><span class="ratio-tooltip" role="tooltip"><strong>Comment lire cette card</strong><span class="ratio-tip-section">THÈSE - scores sur 100</span><b>Signal industriel</b><span>Traction réelle : demande, backlog, capacité, commandes.</span><span class="ratio-benchmark">Repère : &lt;40 faible · 40-60 à confirmer · 60-75 positif · &gt;75 fort</span><b>Confirmation financière</b><span>La traction se retrouve dans les revenus, marges et cash-flows.</span><span class="ratio-benchmark">Repère : &gt;60 confirme la thèse · &gt;75 confirmation forte</span><b>Criticité</b><span>Importance du maillon dans la chaîne de valeur et difficulté à le remplacer.</span><span class="ratio-benchmark">Repère : &gt;70 = maillon particulièrement stratégique</span><b>Valorisation</b><span>Remet le potentiel en regard du prix payé. À lire avec la croissance et la qualité.</span><span class="ratio-benchmark">Repère : &gt;60 favorable · &lt;40 valorisation exigeante</span><b>Diversité des preuves</b><span>Plus les sources indépendantes convergent, plus le signal est robuste.</span><span class="ratio-benchmark">Repère : &gt;60 correct · &gt;75 robuste</span><span class="ratio-tip-section">FONDAMENTAUX</span><b>FCF yield</b><span>FCF / capitalisation. Mesure le cash libre généré pour le prix payé.</span><span class="ratio-benchmark">Repère : &lt;2% exigeant · 2-4% correct si forte croissance · 4-6% attractif · &gt;6% élevé à vérifier</span><b>Marge FCF</b><span>FCF / chiffre d’affaires. Mesure la conversion des ventes en cash libre.</span><span class="ratio-benchmark">Repère : &lt;10% faible · 10-20% solide · &gt;20% très bon · &gt;30% excellent</span><b>ROIC</b><span>Rendement du capital investi. Le point clé est l’écart durable avec le coût du capital.</span><span class="ratio-benchmark">Repère : &lt;8% faible · 8-12% correct · 12-20% très bon · &gt;20% excellent</span><b>CAPEX / OCF</b><span>Part du cash opérationnel réinvestie. Ici, plus bas n’est pas automatiquement meilleur.</span><span class="ratio-benchmark">Repère : &lt;25% léger · 25-50% modéré · &gt;50% très capitalistique ou phase d’investissement</span><b>FCF / action</b><span>Cash libre ramené à une action. L’évolution compte davantage que le niveau absolu.</span><span class="ratio-benchmark">Repère : pas de cible absolue · viser une progression régulière, idéalement &gt;8-10%/an sur plusieurs années</span><b>Croissance FCF</b><span>Tendance pluriannuelle du cash libre. À confronter au FCF yield et à la dilution.</span><span class="ratio-benchmark">Repère : 5-10%/an solide · 10-15% fort · &gt;15% très fort si durable</span><em>Lecture d’ensemble : qualité + croissance + valorisation. Ces seuils sont des ordres de grandeur, pas des règles d’achat. Ils varient selon le secteur, la cyclicité et la phase d’investissement.</em></span></span>';
   sc.insertAdjacentHTML('beforeend','<div class="fund-section-title">Fondamentaux</div><div id="fundCards" class="scoregrid fund-grid"></div>');
   const helpBtn=sc.querySelector('.ratio-help-btn'), tip=sc.querySelector('.ratio-tooltip');
   const positionTip=()=>{
     if(!tip)return;
     const r=sc.getBoundingClientRect(), gap=12, pad=12;
     const w=Math.min(470,Math.max(320,r.left-gap-pad));
     let left=r.left-gap-w;
     if(left<pad) left=pad;
     let top=Math.max(pad,r.top);
     const maxH=Math.max(240,window.innerHeight-top-pad);
     tip.style.setProperty('--ratio-left',`${left}px`);
     tip.style.setProperty('--ratio-top',`${top}px`);
     tip.style.setProperty('--ratio-width',`${w}px`);
     tip.style.setProperty('--ratio-max-height',`${maxH}px`);
   };
   if(helpBtn){
     helpBtn.addEventListener('mouseenter',positionTip);
     helpBtn.addEventListener('focus',positionTip);
     helpBtn.addEventListener('click',e=>{e.stopPropagation();positionTip();const wrap=helpBtn.closest('.ratio-help');const open=wrap.classList.toggle('open');helpBtn.setAttribute('aria-expanded',String(open));});
     window.addEventListener('resize',positionTip);
     document.addEventListener('click',()=>{const wrap=helpBtn.closest('.ratio-help');wrap.classList.remove('open');helpBtn.setAttribute('aria-expanded','false');});
   }
 }
 if(!document.getElementById('fundCompactStyle')){
   const style=document.createElement('style'); style.id='fundCompactStyle'; style.textContent=`
   .scorecard.with-fundamentals{display:flex;flex-direction:column;gap:5px;overflow:visible;position:relative}
   .scorecard.with-fundamentals>h3{margin-bottom:2px;display:flex;align-items:center;justify-content:space-between;gap:8px}
   .scorecard.with-fundamentals>.scoregrid{grid-template-columns:repeat(3,minmax(0,1fr));gap:5px}
   .scorecard.with-fundamentals .score{padding:6px 7px;min-height:47px;display:flex;flex-direction:column;justify-content:center;min-width:0}
   .scorecard.with-fundamentals .score b{font-size:.98rem;line-height:1.08;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
   .scorecard.with-fundamentals .score span{font-size:.59rem;line-height:1.15;margin-top:4px;white-space:normal}
   .scorecard.with-fundamentals .thesis{margin-top:1px;padding-top:5px;flex:0 0 auto}
   .fund-section-title{margin-top:1px;padding-top:5px;border-top:1px solid var(--rule);font-size:.63rem;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);font-weight:800}
   .scorecard.with-fundamentals .fund-grid{margin-top:0!important}
   .ratio-help{position:relative;display:inline-flex;flex:0 0 auto}
   .ratio-help-btn{width:20px;height:20px;padding:0;border-radius:50%;display:grid;place-items:center;background:var(--panel2);border:1px solid var(--accent);color:var(--accent);font-size:.72rem;font-weight:900;line-height:1}
   .ratio-help-btn:hover,.ratio-help.open .ratio-help-btn{background:var(--accent);color:var(--bg)}
   .ratio-tooltip{display:none;position:fixed;z-index:80;left:var(--ratio-left,12px);top:var(--ratio-top,12px);width:var(--ratio-width,470px);max-height:var(--ratio-max-height,72vh);overflow:auto;padding:14px 15px;background:#101719;border:1px solid var(--accent);border-radius:9px;box-shadow:0 12px 32px rgba(0,0,0,.45);color:#d4dddc;font-size:.79rem;line-height:1.42;font-weight:400;text-align:left}
   .ratio-help:hover .ratio-tooltip,.ratio-help:focus-within .ratio-tooltip,.ratio-help.open .ratio-tooltip{display:grid;grid-template-columns:1fr;gap:2px}
   .ratio-tooltip strong{font-size:.98rem;color:var(--ink);margin-bottom:4px}
   .ratio-tooltip b{color:var(--accent);font-size:.8rem;margin-top:6px}
   .ratio-tooltip .ratio-tip-section{margin-top:9px;padding-top:7px;border-top:1px solid var(--rule);color:var(--amber);font-size:.69rem;letter-spacing:.1em;font-weight:900}
   .ratio-tooltip .ratio-benchmark{color:#e4bd68;font-size:.73rem;font-weight:700;margin:1px 0 3px}
   .ratio-tooltip em{margin-top:10px;padding:8px 9px;border-radius:6px;background:var(--panel2);color:var(--ink);font-size:.75rem;line-height:1.4;font-style:normal;font-weight:700}
   @media(max-width:1100px){.scorecard.with-fundamentals>.scoregrid{grid-template-columns:repeat(2,minmax(0,1fr))}.scorecard.with-fundamentals .score{min-height:43px;padding:5px 6px}.scorecard.with-fundamentals .score b{font-size:.9rem}}
   @media(max-width:850px){.scorecard.with-fundamentals{overflow:visible}.scorecard.with-fundamentals>.scoregrid{grid-template-columns:repeat(2,minmax(0,1fr))}.ratio-tooltip{left:16px!important;right:16px;top:16px!important;width:auto!important;max-height:80vh!important;font-size:.82rem}}
   `; document.head.appendChild(style);
 }
 document.getElementById('fundMetric')?.addEventListener('change',renderFundamentals);
}
function renderFundamentals(){
 const c=AIS_FUND.companies?.[selected]; if(!c)return;
 const l=c.latest||{}, cards=[['FCF yield',l.fcf_yield_pct,'%'],['Marge FCF',l.fcf_margin_pct,'%'],['ROIC',l.roic_pct,'%'],['CAPEX / OCF',l.capex_ocf_pct,'%'],['FCF/action',l.fcf_per_share,''],['Croissance FCF',l.fcf_cagr_available_pct,'%']];
 const box=document.getElementById('fundCards'); if(box) box.innerHTML=cards.map(x=>`<div class="score"><b title="${ffmt(x[1],x[2])}">${ffmt(x[1],x[2])}</b><span>${x[0]}</span></div>`).join('');
 if(!priceChart)return; priceChart.data.datasets=priceChart.data.datasets.filter(d=>d.aisFund!==true); delete priceChart.options.scales.y1;
 const key=document.getElementById('fundMetric')?.value; if(key&&c.annual?.length){
   const map=new Map(c.annual.filter(x=>x[key]!=null).map(x=>[String(x.year),x[key]]));
   const vals=priceChart.data.labels.map(d=>map.get(String(d).slice(0,4))??null);
   priceChart.data.datasets.push({label:F_METRICS[key][0],data:vals,borderColor:'#dbb05a',backgroundColor:'transparent',pointRadius:2,spanGaps:true,yAxisID:'y1',aisFund:true});
   priceChart.options.scales.y1={position:'right',ticks:{color:'#dbb05a',font:{size:9}},grid:{drawOnChartArea:false}};
 }
 priceChart.update();
}
fetch('/data/fundamentals.json').then(r=>r.ok?r.json():{companies:{}}).then(d=>{AIS_FUND=d;addFundUI();renderFundamentals()}).catch(()=>{});
const _aisRender=render; render=function(){_aisRender();setTimeout(renderFundamentals,0)};
