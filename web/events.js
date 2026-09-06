const $ = id => document.getElementById(id);
const el = (tag, text, cls) => { const n=document.createElement(tag); if(text!==undefined)n.textContent=text; if(cls)n.className=cls; return n; };
function value(v, suffix='%') { return v===null || v===undefined ? '—' : `${v>0?'+':''}${Number(v).toFixed(2)}${suffix}`; }
function metric(v,suffix='%') { return el('span',value(v,suffix),`metric ${v==null?'placeholder':v>0?'up':v<0?'down':''}`); }
async function get(path,signal) { const r=await fetch(path,{signal}); if(!r.ok)throw new Error(`Request failed (${r.status})`);return r.json(); }
let type='', listRequest, detailRequest;
async function loadEvents() {
  listRequest?.abort(); const controller=new AbortController();listRequest=controller;
  $('status').textContent='Loading events…';$('event-rows').replaceChildren();$('retry').hidden=true;
  const params=new URLSearchParams({limit:'100'});
  for(const [k,v] of [['event_type',type],['ticker',$('ticker').value],['year',$('year').value],['pattern',$('pattern').value]])if(v)params.set(k,v);
  try {
    const data=await get(`/events?${params}`,controller.signal);
    for(const event of data.items){
      const tr=el('tr');tr.dataset.id=event.candidate_id;
      tr.append(el('td',event.event_date,'date'),el('td',event.ticker,'ticker'));
      const cell=el('td'), button=el('button',event.headline,'event-title event-button');button.addEventListener('click',()=>showEvent(event.candidate_id));
      cell.append(button,el('div',[event.event_type,event.fiscal_quarter,event.metrics.calculated_pattern||'No automatic EPS classification'].filter(Boolean).join(' · '),'event-type'));
      tr.append(cell);for(const v of [event.metrics.eps_surprise_pct,event.metrics.return_1d_pct]){const td=el('td');td.append(metric(v));tr.append(td);} $('event-rows').append(tr);
    }
    $('status').textContent=data.total?`${data.total} matching events · Select an event for details and prices.`:'No events match these filters.';
  } catch(e){if(e.name!=='AbortError'){$('status').textContent='Events could not be loaded. Check that the service is running and try again.';$('retry').hidden=false;}}
}
function source(parent,label,url){if(!url)return;try{if(new URL(url).protocol!=='https:')return;}catch{return;}const a=el('a',label);a.href=url;a.target='_blank';a.rel='noopener noreferrer';parent.append(a);}
async function showEvent(id){
 detailRequest?.abort();const controller=new AbortController();detailRequest=controller;
 const body=$('detail-content');body.replaceChildren(el('h2','Loading event…'));if(!$('detail').open)$('detail').showModal();
 try {
  const [e,p]=await Promise.all([get(`/events/${id}`,controller.signal),get(`/events/${id}/prices?before=5&after=5`,controller.signal)]);
  body.replaceChildren(el('h2',`${e.ticker} · ${e.headline}`));body.firstChild.id='detail-title';
  const m=e.metrics;
  body.append(el('p',`Announcement: ${e.event_date} (${e.release_timing}) · Reaction: ${m.reaction_date} · Fifth session: ${m.fifth_session}`));
  const metrics=el('div',undefined,'detail-metrics');
  for(const [label,v,suffix] of [['EPS surprise',m.eps_surprise_pct,'%'],['1D return',m.return_1d_pct,'%'],['5D return',m.return_5d_pct,'%'],[`1D excess vs ${m.benchmark}`,m.excess_return_1d_pp,' pp'],['Volume vs prior 60 sessions',m.volume_ratio_60d,'×']]){const box=el('div');box.append(el('b',label),metric(v,suffix));metrics.append(box);}body.append(metrics);
  body.append(el('p',`Calculated pattern: ${m.calculated_pattern||'Not classified'}. ${m.eps_eligible?'Comparable EPS inputs admitted.':'Automatic EPS analysis is unavailable for this event.'}`),el('p',e.why_selected),el('p',e.timing_notes));
  if(e.estimate){const x=e.estimate;body.append(el('p',`Research EPS: actual ${x.actual_eps} (${x.actual_eps_basis}); consensus ${x.consensus_eps} (${x.consensus_eps_basis}). Comparability verified: ${x.comparability_verified?'yes':'no'}.`),el('p',x.notes));}
  const links=el('div',undefined,'source-links');source(links,'Event source',e.source_url);source(links,'Timing evidence',e.timing_source_url);source(links,'Actual EPS',e.estimate?.actual_source_url);source(links,'Consensus',e.estimate?.consensus_source_url);body.append(links);
  body.append(el('h3','Adjusted closing prices'),el('p',`Five sessions before the reaction and five including it. Benchmark: ${p.benchmark}.`));
  const wrap=el('div',undefined,'price-scroll'),table=el('table',undefined,'price-table'),head=el('tr');for(const label of ['Date','Ticker','Adjusted close','Volume'])head.append(el('th',label));const thead=el('thead');thead.append(head);table.append(thead);const tbody=el('tbody');
  for(const r of p.items){const tr=el('tr');for(const v of [r.price_date,r.ticker,r.adjusted_close==null?'—':Number(r.adjusted_close).toFixed(4),r.volume==null?'—':Number(r.volume).toLocaleString()])tr.append(el('td',v));tbody.append(tr);}table.append(tbody);wrap.append(table);body.append(wrap);
 }catch(e){if(e.name!=='AbortError'){body.replaceChildren(el('h2','Unable to load event'));const retry=el('button','Retry');retry.onclick=()=>showEvent(id);body.append(retry);}}
}
$('close-detail').onclick=()=>$('detail').close();$('detail').addEventListener('close',()=>detailRequest?.abort());
for(const id of ['ticker','year','pattern'])$(id).addEventListener('change',loadEvents);
async function init(){
 try{const [filters,all]=await Promise.all([get('/filters'),get('/events?limit=1')]);$('total').textContent=`${all.total} selected events`;
  for(const [id,values] of [['ticker',filters.tickers],['year',filters.years]]){const select=$(id);while(select.options.length>1)select.remove(1);for(const v of values){const option=el('option',v);option.value=v;select.append(option);}}
  const group=$('type-filters');group.replaceChildren();for(const t of ['',...filters.event_types]){const button=el('button',t?t[0].toUpperCase()+t.slice(1):'All events','chip'+(type===t?' active':''));button.dataset.filter=t;button.setAttribute('aria-pressed',String(type===t));button.onclick=()=>{type=t;for(const b of group.children){b.classList.toggle('active',b===button);b.setAttribute('aria-pressed',String(b===button));}loadEvents();};group.append(button);}await loadEvents();
 }catch{$('total').textContent='Unavailable';$('status').textContent='Unable to connect. Start the service and select Retry.';$('retry').hidden=false;}
}
$('retry').onclick=init;
init();
