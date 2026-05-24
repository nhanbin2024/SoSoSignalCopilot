const $ = (id) => document.getElementById(id);
const state = { data: null, ai: null, holdings: [] };

function toast(msg){ console.log(msg); }
function esc(v){return String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function label(item){return item.symbol || item.ticker || item.name || item.asset || item.title || item.coin || item.currency || 'SoSo record';}
function value(item){return item.price ?? item.change24h ?? item.change ?? item.netFlow ?? item.net_inflow ?? item.sentiment ?? item.status ?? item.date ?? '';}
function fmt(v){ if(typeof v==='number'){ if(Math.abs(v)>=1e9)return `$${(v/1e9).toFixed(2)}B`; if(Math.abs(v)>=1e6)return `$${(v/1e6).toFixed(2)}M`; return String(Math.round(v*100)/100);} return String(v ?? '');}
function live(block){return block?.source === 'sosovalue-api' && (block?.itemCount || 0) > 0;}

function switchTab(id){ document.querySelectorAll('.tab').forEach(x=>x.classList.remove('show')); $(id).classList.add('show'); document.querySelectorAll('.nav').forEach(x=>x.classList.toggle('active', x.dataset.tab===id)); }
document.querySelectorAll('.nav').forEach(btn=>btn.onclick=()=>switchTab(btn.dataset.tab));
$('openApi').onclick=()=>switchTab('api');

function rows(id, block){
  const el=$(id); const items=block?.items || [];
  el.innerHTML = items.slice(0,8).map(item=>`<div class="row"><div><b>${esc(label(item))}</b><small>${esc(JSON.stringify(item).slice(0,130))}</small></div><strong>${esc(fmt(value(item)))}</strong></div>`).join('') || `<div class="row"><div><b>No live records</b><small>${esc(block?.warning || 'Check API Console')}</small></div><strong>${esc(block?.status || '')}</strong></div>`;
}

function signalCard(s){
  return `<article class="signal"><div class="score">${esc(s.score ?? 0)}</div><h4>${esc(s.title)}</h4><p><b>Confidence:</b> ${esc(s.confidence)}</p><ul>${(s.evidence||[]).map(e=>`<li>${esc(e)}</li>`).join('')}</ul><p><b>Invalidation:</b> ${esc(s.invalidation)}</p><p><b>Action:</b> ${esc(s.action)}</p></article>`;
}

function render(){
  const d=state.data || {};
  $('marketCount').textContent=d.market?.itemCount || 0; $('etfCount').textContent=d.etf?.itemCount || 0; $('newsCount').textContent=d.news?.itemCount || 0; $('ssiCount').textContent=d.ssi?.itemCount || 0;
  const count=['market','etf','news','ssi'].filter(k=>live(d[k])).length;
  $('liveScore').textContent=`${count}/4`;
  $('apiBadge').textContent=count ? 'Live SoSo API' : 'API Error'; $('apiBadge').className=`badge ${count?'good':'bad'}`;
  $('brief').textContent=state.ai?.brief || (count ? 'Live data loaded.' : 'No live SoSoValue records. Open API Console to inspect exact errors.');
  rows('marketRows',d.market); rows('etfRows',d.etf); rows('newsRows',d.news); rows('ssiRows',d.ssi);
  const signals=state.ai?.signals || [];
  $('topSignals').innerHTML=signals.slice(0,3).map(signalCard).join('') || '<p class="brief">No signals until live SoSoValue records are loaded.</p>';
  $('signalList').innerHTML=signals.map(signalCard).join('') || '<p class="brief">No signals until live SoSoValue records are loaded.</p>';
  $('radarList').innerHTML=(state.ai?.radar || []).map(r=>`<div class="radar-row"><b>${esc(r.name)}</b><div class="bar"><i style="width:${Math.max(0,Math.min(100,r.heat))}%"></i></div><span>${esc(r.heat)}/100</span></div>`).join('') || '<p class="brief">No radar until live data loads.</p>';
  const a=state.ai?.allocation;
  $('allocation').innerHTML=a?.allocations?.length ? a.allocations.map(x=>`<div class="alloc-row"><b>${esc(x.name)}</b><div class="bar"><i style="width:${x.weight}%"></i></div><span>${x.weight}%</span></div>`).join('') + `<p class="brief">${esc(a.note)}</p>` : `<p class="brief">${esc(a?.note || 'No live SSI allocation yet.')}</p>`;
  const pr=state.ai?.portfolioRisk;
  $('riskBox').innerHTML=pr ? `<div class="brief"><h3>Risk Score: ${esc(pr.score)}/100</h3><p>Concentration: ${esc(pr.concentration)}</p><p>SSI Exposure: ${esc(pr.ssiExposure)}%</p><p>${esc(pr.suggestion)}</p></div>` : '';
}

function parseHoldings(){
  return $('holdings').value.split('\n').map(line=>line.trim()).filter(Boolean).map(line=>{const parts=line.split(/\s+/); const weight=Number(parts.pop().replace('%','')); return {asset:parts.join(' '), weight:Number.isFinite(weight)?weight:0};});
}

async function analyze(){
  const res=await fetch('/api/ai',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({data:state.data, holdings:parseHoldings(), profile:$('profile').value})});
  state.ai=await res.json(); render();
}

async function refresh(){
  $('apiBadge').textContent='Loading';
  const res=await fetch('/api/soso?resource=all',{cache:'no-store'});
  const json=await res.json();
  state.data={market:json.market,etf:json.etf,news:json.news,ssi:json.ssi};
  $('apiLog').textContent=JSON.stringify(json,null,2);
  await analyze();
}

$('refresh').onclick=refresh;
$('profile').onchange=analyze;
$('analyzePortfolio').onclick=analyze;
$('explore').onclick=async()=>{const r=await fetch('/api/soso?resource=explore',{cache:'no-store'}); $('apiLog').textContent=JSON.stringify(await r.json(),null,2); switchTab('api');};
$('testPath').onclick=async()=>{const p=$('customPath').value.trim(); if(!p)return; const r=await fetch('/api/soso?path='+encodeURIComponent(p),{cache:'no-store'}); $('apiLog').textContent=JSON.stringify(await r.json(),null,2);};
$('exportMd').onclick=()=>{
  const md=[`# SoSo Signal Copilot v2 Research Plan`, '', `Generated: ${new Date().toISOString()}`, '', `## Brief`, state.ai?.brief || '', '', `## Signals`, ...(state.ai?.signals||[]).flatMap(s=>[`### ${s.title}`,`Score: ${s.score}/100`, `Confidence: ${s.confidence}`, ...(s.evidence||[]).map(e=>`- ${e}`), `Invalidation: ${s.invalidation}`, `Action: ${s.action}`, '']), '', 'Disclaimer: research only, not financial advice.'].join('\n');
  const blob=new Blob([md],{type:'text/markdown'}); const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download='soso-signal-plan.md'; a.click(); URL.revokeObjectURL(a.href);
};
refresh();
