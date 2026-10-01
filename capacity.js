// AI CAPACITY — Capacity Monitor v0.1 overlay. EXPERIMENTAL, NON SCORING.
// Self-contained: reads only /data/capacity/snapshots.json and shares no state
// with the Signal Score scripts.
(function(){
  'use strict';
  var SNAPSHOTS=[];
  function esc(v){return String(v==null?'':v).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
  function num(v,d){return v==null?'<span class="cap-null">—</span>':Number(v).toLocaleString('fr-FR',{maximumFractionDigits:d==null?2:d})}
  function table(head,rows,textCols){return '<table class="cap-table"><thead><tr>'+head.map(function(h,i){return '<th'+(i&&!(textCols||[]).includes(i)?' class="num"':'')+'>'+h+'</th>'}).join('')+'</tr></thead><tbody>'+rows.join('')+'</tbody></table>'}
  function section(title,note,body){return '<section class="cap-section"><h3>'+title+'</h3>'+(note?'<div class="cap-note">'+note+'</div>':'')+body+'</section>'}

  function buildout(s){
    var years=Object.keys(s.buildout.years),demandYears=s.demand.years;
    var rows=[['announced_gw','Announced (C0–C5)'],['committed_gw','Committed (C3–C5)'],['effective_gw','Effective'],['operational_gw','Operational (C5)']].map(function(r){
      return '<tr><td>'+r[1]+'</td>'+years.map(function(y){return '<td class="num">'+num(s.buildout.years[y][r[0]])+'</td>'}).join('')+'</tr>'});
    ['bear','base','bull'].forEach(function(sc){rows.push('<tr class="cap-demand"><td>Demand '+sc+'</td>'+years.map(function(y){return '<td class="num">'+num(demandYears[y][sc])+'</td>'}).join('')+'</tr>')});
    return section('Physical Buildout 2026–2030','Unité : '+esc(s.buildout.unit)+'. Stock disponible par millésime. « — » = inconnu, jamais estimé.',table(['GW_IT'].concat(years),rows));
  }
  function stress(s){
    var years=Object.keys(s.absorption_stress);
    var rows=['bear','base','bull'].map(function(sc){return '<tr><td>AS_'+sc+'</td>'+years.map(function(y){var c=s.absorption_stress[y][sc];return '<td class="num" title="'+esc(c.reason||'')+'">'+num(c.value,3)+'</td>'}).join('')+'</tr>'});
    return section('Absorption Stress','AS = capacité effective / demande indépendante. Ratio de stress, pas un indicateur de krach : aucun seuil automatique.',table(['Scénario'].concat(years),rows));
  }
  function ladder(s){
    var rows=['C0','C1','C2','C3','C4','C5','X','UNKNOWN'].map(function(l){var c=s.ladder[l];return '<tr><td>'+l+'</td><td class="num">'+c.projects+'</td><td class="num">'+num(c.gw)+'</td><td class="num">'+c.non_canonical_projects+'</td></tr>'});
    return section('Commitment Ladder','Committed = C3+C4+C5 · Operational = C5 · aucune pondération probabiliste en v0.1.',table(['Niveau','Projets','GW_IT','Hors unité'],rows));
  }
  function assessments(list){
    if(!list.length)return '<div class="cap-null">Aucune évaluation.</div>';
    return list.map(function(a){return '<div class="cap-assess"><b>'+esc(a.node)+' : '+esc(a.value)+'</b><div>'+esc(a.justification)+'</div>'+(a.relations?'<div class="cap-note">Relations : '+a.relations.map(esc).join(' · ')+'</div>':'')+'<div class="cap-note"><a href="'+esc(a.source.url)+'" target="_blank" rel="noopener">source</a> · observé '+esc(String(a.observed_at).slice(0,10))+'</div></div>'}).join('');
  }
  function risk(s){
    var r=s.system_risk,t=r.T.realized_months;
    var body='<div class="cap-grid">'+
      '<div class="cap-card"><h4>E · Supply Elasticity</h4>'+assessments(r.E)+'</div>'+
      '<div class="cap-card"><h4>C · Supply Commitment</h4><div>Committed : '+num(r.C.committed_gw)+' GW_IT</div><div>Operational : '+num(r.C.operational_gw)+' GW_IT</div></div>'+
      '<div class="cap-card"><h4>T · Time-to-Supply</h4><div>Délai réalisé engagement → mise en service (mois) : médiane '+num(t.median,1)+' · IQR '+(t.p25==null?num(null):num(t.p25,1)+'–'+num(t.p75,1))+' · n='+t.n+'</div></div>'+
      '<div class="cap-card"><h4>D · Demand Reality Gap</h4><div>Voir Absorption Stress.</div></div>'+
      '<div class="cap-card"><h4>F · Financing Independence</h4>'+assessments(r.F)+'</div></div>';
    var hist=SNAPSHOTS.map(function(x){
      function q(c){return x.system_risk[c].map(function(a){return esc(a.node)+':'+esc(a.value)}).join(', ')||'—'}
      var d=Object.keys(x.absorption_stress).filter(function(y){return x.absorption_stress[y].base.value!=null}).map(function(y){return y+' : '+num(x.absorption_stress[y].base.value,3)}).join(' · ')||num(null);
      return '<tr><td>'+esc(x.weekly_snapshot_date)+'</td><td>'+q('E')+'</td><td class="num">'+num(x.system_risk.C.committed_gw)+'</td><td class="num">'+num(x.system_risk.T.realized_months.median,1)+'</td><td class="num">'+d+'</td><td>'+q('F')+'</td></tr>'});
    return section('System Risk E-C-T-D-F','Cinq dimensions affichées séparément, jamais agrégées en score.',body+'<h4 class="cap-sub">Historique PIT (une ligne par période hebdomadaire)</h4>'+table(['Période','E','C committed GW_IT','T médiane (mois)','D = AS_base par millésime','F'],hist.reverse(),[1,5]));
  }
  function render(){
    var body=document.getElementById('capBody');if(!body)return;
    if(!SNAPSHOTS.length){body.innerHTML='<div class="cap-null" style="padding:22px">Aucun snapshot Capacity figé pour le moment.</div>';return}
    var s=SNAPSHOTS[SNAPSHOTS.length-1];
    document.getElementById('capMeta').textContent='Snapshot '+s.capacity_snapshot_captured_at.slice(0,16).replace('T',' ')+' UTC · après freeze Signal du '+s.weekly_snapshot_date+' · '+s.method_version+' · '+s.counts.observations+' observation(s)'+(s.counts.historical_seed?' dont '+s.counts.historical_seed+' historical seed':'');
    body.innerHTML=buildout(s)+stress(s)+ladder(s)+risk(s);
  }
  // Third mode tab next to "Radar" and "Portefeuille virtuel" (created by
  // portfolio.js). Only DOM classes are shared; no Signal Score state is read.
  function main(){return document.querySelector('.main')}
  function view(){
    var m=main();if(!m)return null;
    var v=m.querySelector('.capacity-view');
    if(!v){v=document.createElement('div');v.className='capacity-view';
      v.innerHTML='<div class="cap-banner">SHADOW MODEL — EXPERIMENTAL — NON SCORING<span>Generated after the weekly signal freeze. Not used in the Signal Score. Indicateur de recherche indépendant.</span></div>'+
        '<header class="cap-head"><div><div class="eyebrow">Capacity Monitor v0.1</div><h2 id="capTitle">AI Capacity</h2><div class="cap-note" id="capMeta"></div></div></header><div id="capBody"></div>';
      m.appendChild(v)}
    return v;
  }
  function enter(){
    var m=main();if(!m||!view())return;
    document.querySelectorAll('.mode-tab').forEach(function(b){b.classList.toggle('active',b.dataset.mode==='capacity')});
    document.body.classList.remove('portfolio-mode');m.classList.remove('portfolio-active');
    document.body.classList.add('capacity-mode');m.classList.add('capacity-active');render();
  }
  function leave(){var m=main();document.body.classList.remove('capacity-mode');if(m)m.classList.remove('capacity-active')}
  function installTab(tabs){
    if(!tabs||tabs.querySelector('[data-mode="capacity"]'))return;
    var b=document.createElement('button');b.className='mode-tab cap-tab';b.dataset.mode='capacity';b.type='button';b.textContent='AI Capacity';b.title='Shadow model expérimental, non utilisé dans le Signal Score';
    b.addEventListener('click',enter);tabs.appendChild(b);
    tabs.addEventListener('click',function(e){var t=e.target.closest('.mode-tab');if(t&&t.dataset.mode!=='capacity')leave()},true);
  }
  function setup(){
    if(document.getElementById('capStyle'))return;
    document.head.insertAdjacentHTML('beforeend','<style id="capStyle">'+
      '.cap-tab{border-color:rgba(219,176,90,.55)}.cap-tab.active{border-color:var(--amber);color:var(--amber)}'+
      '.capacity-view{display:none}.main.capacity-active{display:block;overflow:auto}.main.capacity-active>:not(.capacity-view){display:none!important}.main.capacity-active>.capacity-view{display:block}'+
      'body.capacity-mode .sidebar>.search,body.capacity-mode .sidebar>.sidefilters,body.capacity-mode #tickerNav{display:none!important}'+
      '.cap-banner{background:rgba(219,176,90,.14);border:1px solid var(--amber);border-radius:10px;padding:10px 16px;color:var(--amber);font-weight:900;letter-spacing:.06em}.cap-banner span{display:block;font-weight:600;letter-spacing:0;color:var(--ink);font-size:.8rem}'+
      '.cap-head{padding:12px 0 6px;border-bottom:1px solid var(--rule)}.cap-head h2{margin:2px 0 4px;font-size:clamp(1.7rem,2.8vw,2.5rem)}'+
      '#capBody{padding-bottom:18px}.cap-section{padding:14px 0;border-bottom:1px solid var(--rule)}.cap-section h3{margin:0 0 4px}.cap-sub{margin:12px 0 4px}'+
      '.cap-note,.cap-null{color:var(--muted);font-size:.76rem}.cap-table{min-width:0;margin-top:6px}.cap-table td,.cap-table th{padding:5px 8px}.cap-table th.num{text-align:right}.capacity-view a{color:var(--accent)}.cap-demand td{color:var(--blue)}'+
      '.cap-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:8px;margin-top:6px}.cap-card{background:var(--panel2);border:1px solid var(--rule);border-radius:8px;padding:9px}.cap-card h4{margin:0 0 6px;color:var(--amber);font-size:.78rem}.cap-assess{margin-bottom:6px}'+
      '</style>');
    var tabs=document.getElementById('modeTabs');
    if(tabs){installTab(tabs);return}
    // portfolio.js is loaded asynchronously by markers.js: wait for its tabs.
    var obs=new MutationObserver(function(){var t=document.getElementById('modeTabs');if(t){obs.disconnect();installTab(t)}});
    obs.observe(document.body,{childList:true,subtree:true});
    setTimeout(function(){
      if(document.getElementById('modeTabs'))return;
      obs.disconnect();var brand=document.querySelector('.brand');if(!brand)return;
      var t=document.createElement('div');t.id='modeTabs';t.className='mode-tabs';t.style.cssText='display:flex;gap:5px;margin-top:9px';
      t.innerHTML='<button class="mode-tab active" data-mode="radar" type="button">Radar</button>';brand.appendChild(t);installTab(t);
    },5000);
  }
  setup();
  fetch('/data/capacity/snapshots.json',{cache:'no-store'}).then(function(r){return r.ok?r.json():[]}).then(function(d){SNAPSHOTS=Array.isArray(d)?d:[];render()}).catch(function(){SNAPSHOTS=[];render()});
})();
