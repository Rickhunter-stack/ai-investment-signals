let AIS_FUND={companies:{}};
const F_METRICS={fcf_per_share:['FCF / action','€/$ par action'],fcf_margin_pct:['Marge FCF','%'],roic_pct:['ROIC','%'],capex_ocf_pct:['CAPEX / OCF','%'],fcf_yield_pct:['FCF yield','%']};
function ffmt(v,s=''){return v==null?'—':Number(v).toLocaleString('fr-FR',{maximumFractionDigits:2})+s}
function addFundUI(){
 const pc=document.querySelector('.pricecard h3'); if(pc&&!document.getElementById('fundMetric')) pc.innerHTML='Cotation & fondamentaux <select id="fundMetric" style="float:right"><option value="">Cours seul</option>'+Object.entries(F_METRICS).map(([k,v])=>`<option value="${k}">${v[0]}</option>`).join('')+'</select>';
 const sc=document.querySelector('.scorecard');
 if(sc&&!document.getElementById('fundCards')){
   sc.classList.add('with-fundamentals');
   sc.insertAdjacentHTML('beforeend','<div class="fund-section-title">Fondamentaux</div><div id="fundCards" class="scoregrid fund-grid"></div>');
 }
 if(!document.getElementById('fundCompactStyle')){
   const style=document.createElement('style'); style.id='fundCompactStyle'; style.textContent=`
   .scorecard.with-fundamentals{display:flex;flex-direction:column;gap:5px;overflow:hidden}
   .scorecard.with-fundamentals>h3{margin-bottom:2px}
   .scorecard.with-fundamentals>.scoregrid{grid-template-columns:repeat(3,minmax(0,1fr));gap:5px}
   .scorecard.with-fundamentals .score{padding:6px 7px;min-height:47px;display:flex;flex-direction:column;justify-content:center;min-width:0}
   .scorecard.with-fundamentals .score b{font-size:.98rem;line-height:1.08;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
   .scorecard.with-fundamentals .score span{font-size:.59rem;line-height:1.15;margin-top:4px;white-space:normal}
   .scorecard.with-fundamentals .thesis{margin-top:1px;padding-top:5px;flex:0 0 auto}
   .fund-section-title{margin-top:1px;padding-top:5px;border-top:1px solid var(--rule);font-size:.63rem;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);font-weight:800}
   .scorecard.with-fundamentals .fund-grid{margin-top:0!important}
   @media(max-width:1100px){.scorecard.with-fundamentals>.scoregrid{grid-template-columns:repeat(2,minmax(0,1fr))}.scorecard.with-fundamentals .score{min-height:43px;padding:5px 6px}.scorecard.with-fundamentals .score b{font-size:.9rem}}
   @media(max-width:850px){.scorecard.with-fundamentals{overflow:visible}.scorecard.with-fundamentals>.scoregrid{grid-template-columns:repeat(2,minmax(0,1fr))}}
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
