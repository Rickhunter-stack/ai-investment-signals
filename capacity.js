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
  function open(){var o=document.getElementById('capOverlay');if(!o)return;o.classList.add('open');o.setAttribute('aria-hidden','false');render()}
  function close(){var o=document.getElementById('capOverlay');if(!o)return;o.classList.remove('open');o.setAttribute('aria-hidden','true')}
  function setup(){
    if(document.getElementById('capOverlay'))return;
    document.head.insertAdjacentHTML('beforeend','<style>'+
      '.cap-open{border-color:var(--amber);color:var(--amber);font-weight:800;margin-top:6px}'+
      '.cap-overlay{display:none;position:fixed;inset:0;z-index:150;background:rgba(3,8,10,.85);padding:3vh 3vw}.cap-overlay.open{display:flex;justify-content:center}'+
      '.cap-modal{width:min(1240px,96vw);max-height:94vh;display:flex;flex-direction:column;background:#101719;border:1px solid var(--amber);border-radius:14px;overflow:hidden}'+
      '.cap-banner{background:rgba(219,176,90,.14);border-bottom:1px solid var(--amber);padding:10px 20px;color:var(--amber);font-weight:900;letter-spacing:.06em}.cap-banner span{display:block;font-weight:600;letter-spacing:0;color:var(--ink);font-size:.8rem}'+
      '.cap-head{display:flex;justify-content:space-between;gap:16px;padding:12px 20px;border-bottom:1px solid var(--rule)}.cap-head h2{margin:0;font-size:1.3rem}'+
      '#capBody{overflow:auto;padding:4px 20px 20px}.cap-section{padding:14px 0;border-bottom:1px solid var(--rule)}.cap-section h3{margin:0 0 4px}.cap-sub{margin:12px 0 4px}'+
      '.cap-note,.cap-null{color:var(--muted);font-size:.76rem}.cap-table{min-width:0;margin-top:6px}.cap-table td,.cap-table th{padding:5px 8px}.cap-table th.num{text-align:right}.cap-overlay a{color:var(--accent)}.cap-demand td{color:var(--blue)}'+
      '.cap-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:8px;margin-top:6px}.cap-card{background:var(--panel2);border:1px solid var(--rule);border-radius:8px;padding:9px}.cap-card h4{margin:0 0 6px;color:var(--amber);font-size:.78rem}.cap-assess{margin-bottom:6px}'+
      '</style>');
    var top=document.querySelector('.topbar > div:last-child')||document.body;
    top.insertAdjacentHTML('beforeend','<div><button class="cap-open" id="capOpen" type="button">AI CAPACITY · shadow</button></div>');
    document.body.insertAdjacentHTML('beforeend','<div class="cap-overlay" id="capOverlay" aria-hidden="true"><section class="cap-modal" role="dialog" aria-modal="true" aria-labelledby="capTitle">'+
      '<div class="cap-banner">SHADOW MODEL — EXPERIMENTAL — NON SCORING<span>Generated after the weekly signal freeze. Not used in the Signal Score. Indicateur de recherche indépendant.</span></div>'+
      '<header class="cap-head"><div><h2 id="capTitle">AI Capacity</h2><div class="cap-note" id="capMeta"></div></div><button class="brief-archive-close" id="capClose" type="button" aria-label="Fermer">×</button></header>'+
      '<div id="capBody"></div></section></div>');
    document.getElementById('capOpen').addEventListener('click',open);
    document.getElementById('capClose').addEventListener('click',close);
    document.getElementById('capOverlay').addEventListener('click',function(e){if(e.target===e.currentTarget)close()});
    document.addEventListener('keydown',function(e){if(e.key==='Escape')close()});
  }
  setup();
  fetch('/data/capacity/snapshots.json',{cache:'no-store'}).then(function(r){return r.ok?r.json():[]}).then(function(d){SNAPSHOTS=Array.isArray(d)?d:[];render()}).catch(function(){SNAPSHOTS=[];render()});
})();
