// Run after building the dashboard AND injecting brief memory.
// DOM/Chart doubles exercise real generated JS, not browser layout.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const page = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
assert(!page.includes('id="readout"'), 'Run inject_brief_memory.py first');
const inline = page.split('<script>')[1].split('</script>')[0];
const nodes = new Map(), listeners = new Map();
let events = 0;
function node() {
  return {value:'', innerHTML:'', textContent:'', appendChild(){},
    classList:{remove(){},add(){}}, dataset:{}};
}
const document = {
  getElementById(id) {
    if(id === 'readout') return null;
    if(!nodes.has(id)) nodes.set(id,node());
    return nodes.get(id);
  },
  createElement:node, querySelectorAll(){return [];},
  addEventListener(name, fn){listeners.set(name,fn);},
  dispatchEvent(event){events++; listeners.get(event.type)?.(event);}
};
const context = vm.createContext({
  document, CustomEvent:function(type,init){this.type=type;this.detail=init.detail;},
  // Keep fetch pending: use repository fixtures explicitly below.
  fetch:()=>new Promise(()=>{}),
  Chart:function(el,cfg){
    this.data=cfg.data;this.options=cfg.options;
    this.destroy=()=>{};this.update=()=>{};
  }
});
vm.runInContext(inline, context);
vm.runInContext(fs.readFileSync(path.join(root,'fundamentals.js'),'utf8'),context);
const fixture=JSON.parse(fs.readFileSync(path.join(root,'data/fundamentals.json'),'utf8'));
context.fixture=fixture;
vm.runInContext('AIS_FUND=fixture',context);
for(const ticker of ['NVDA','MSFT','TSLA','REGN','NVDA']){
  vm.runInContext("selectTicker("+JSON.stringify(ticker)+")",context);
  assert.equal(nodes.get('tickerLabel').textContent,'('+ticker+')');
  const latest=fixture.companies[ticker].latest;
  const expected=[latest.fcf_yield_pct,latest.fcf_margin_pct,latest.roic_pct,
    latest.capex_ocf_pct,latest.fcf_per_share,latest.fcf_cagr_available_pct];
  const actual=[...nodes.get('fundCards').innerHTML.matchAll(/<b[^>]*>(.*?)<\/b>/g)].map(m=>m[1]);
  const formatted=expected.map((v,i)=>v==null?'—':Number(v).toLocaleString('fr-FR',{maximumFractionDigits:2})+(i===4?'':'%'));
  assert.deepEqual(actual,formatted,ticker+' fundamentals');
  console.log(ticker+': '+actual.join(' | '));
}
assert.equal(events,5);
assert(nodes.get('corrNote').textContent, 'Correlation initialized');
console.log('PASS: five selections, correct fundamentals, no missing-readout exception.');
