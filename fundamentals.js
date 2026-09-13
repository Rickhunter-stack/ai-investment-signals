let AIS_FUND={companies:{}};
const F_METRICS={fcf_per_share:['FCF / action','€/$ par action'],fcf_margin_pct:['Marge FCF','%'],roic_pct:['ROIC','%'],capex_ocf_pct:['CAPEX / OCF','%'],fcf_yield_pct:['FCF yield','%']};
function ffmt(v,s=''){return v==null?'—':Number(v).toLocaleString('fr-FR',{maximumFractionDigits:2})+s}
function addFundUI(){
 const pc=document.querySelector('.pricecard h3'); if(pc&&!document.getElementById('fundMetric')) pc.innerHTML='Cotation & fondamentaux <select id="fundMetric" style="float:right"><option value="">Cours seul</option>'+Object.entries(F_METRICS).map(([k,v])=>`<option value="${k}">${v[0]}</option>`).join('')+'</select>';
 const sc=document.querySelector('.scorecard'); if(sc&&!document.getElementById('fundCards')) sc.insertAdjacentHTML('beforeend','<div id="fundCards" class="scoregrid" style="margin-top:7px"></div>');
 document.getElementById('fundMetric')?.addEventListener('change',renderFundamentals);
}
function renderFundamentals(){
 const c=AIS_FUND.companies?.[selected]; if(!c)return;
 const l=c.latest||{}, cards=[['FCF yield',l.fcf_yield_pct,'%'],['Marge FCF',l.fcf_margin_pct,'%'],['ROIC',l.roic_pct,'%'],['CAPEX / OCF',l.capex_ocf_pct,'%'],['FCF/action',l.fcf_per_share,''],['Croissance FCF',l.fcf_cagr_available_pct,'%']];
 const box=document.getElementById('fundCards'); if(box) box.innerHTML=cards.map(x=>`<div class="score"><b>${ffmt(x[1],x[2])}</b><span>${x[0]}</span></div>`).join('');
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
