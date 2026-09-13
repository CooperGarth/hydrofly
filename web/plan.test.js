// DOM/transport integration, not rendered WebGL verification. Only the renderer
// is stubbed; the actual application handlers and Python HTTP model execute.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {spawn} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {JSDOM} from 'jsdom';
const root=fileURLToPath(new URL('../',import.meta.url));
const base='http://127.0.0.1:8766';
const delay=ms=>new Promise(r=>setTimeout(r,ms));

test('mine-plan controls use real Python, retain learning, and pause training',{timeout:120000},async()=>{
 const child=spawn(process.env.HYDROFLY_TEST_PYTHON||'python',['-m','uvicorn','hydrofly.api:app','--host','127.0.0.1','--port','8766'],{cwd:root,env:{...process.env,HYDROFLY_SKIP_WARMUP:'1'},stdio:['ignore','ignore','pipe']});
 let logs='';child.stderr.on('data',d=>logs+=d);let dom;
 try{
  let ready=false;for(let i=0;i<100;i++){try{if((await fetch(base+'/api/health')).ok){ready=true;break;}}catch{}if(child.exitCode!==null)break;await delay(100);}
  assert.ok(ready,logs);
  dom=new JSDOM(await readFile(new URL('./index.html',import.meta.url),'utf8'),{url:base,runScripts:'outside-only',pretendToBeVisual:true});
  const w=dom.window,requests=[];let permitArrival=true,arrivalCalls=0;
  w.fetch=(path,options)=>{requests.push(path==='/api/portable/learn'?path+'/'+JSON.parse(options.body).operation:path);return fetch(new URL(path,base),options);};
  w.AbortController=AbortController;w.structuredClone=structuredClone;w.matchMedia=()=>({matches:true});
  w.createBrainActivity=()=>({flash(){}});
  const cameraCalls=[];let section=false,surface=true;
  w.createMineScene=()=>({update(){},setActivity(){},focusFly(){cameraCalls.push('fly');},resetCamera(){cameraCalls.push('reset');},toggleSection(){section=!section;return section;},toggleSurface(){surface=!surface;return surface;}});
  let exported;w.Blob=Blob;w.URL.createObjectURL=blob=>{exported=blob;return 'blob:hydrofly-test';};w.URL.revokeObjectURL=()=>{};w.HTMLAnchorElement.prototype.click=()=>{};
  const source=(await readFile(new URL('./plan.js',import.meta.url),'utf8')).replace(/^import .*;\n/gm,'');
  await w.eval(`(async()=>{${source}\n})()`);
  const el=id=>w.document.getElementById(id);
  assert.match(el('activity').textContent,/Plan evaluated/);
  const clicked=new Set();for(const button of w.document.querySelectorAll('button[id]')){const handler=button.onclick;if(handler)button.onclick=function(...args){clicked.add(this.id);return handler.apply(this,args);};}
  const plotted=[...el('level-chart').querySelectorAll('[data-head]')].map(e=>Number(e.dataset.head));
  const rows=[...el('level-values').querySelectorAll('tr')];
  assert.equal(plotted.length,121);
  assert.equal(rows.length,121);
  assert.equal(el('level-chart').querySelectorAll('[data-series]').length,3);
  for(const key of ['floor','target']){const path=el('level-chart').querySelector(`[data-series="${key}"]`).getAttribute('d');assert.equal((path.match(/H/g)||[]).length,10);assert.equal((path.match(/V/g)||[]).length,10);assert.ok(!path.includes('L'));}
  assert.equal(w.document.querySelector('.setup').open,false);
  const numerical=await (await fetch(base+'/api/plan/evaluate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({})})).json();
  assert.deepEqual(plotted,numerical.timeline.map(t=>t.head));
  assert.equal(el('stat-drawdown').textContent,`${numerical.statistics.max_drawdown_m.toFixed(2)} m`);
  assert.equal(el('stat-volume').textContent,Math.round(numerical.total_volume).toLocaleString());
  assert.equal(el('stat-cost').textContent,`A$${Math.round(numerical.operating_cost_aud).toLocaleString()}`);
  el('world-view').onclick();assert.ok(w.document.body.classList.contains('world-mode'));el('world-view').onclick();
  el('follow-fly').onclick();el('reset-camera').onclick();assert.deepEqual(cameraCalls,['fly','reset']);
  el('section-view').onclick();assert.equal(el('section-view').textContent,'Orbit view');el('section-view').onclick();
  el('head-toggle').onclick();assert.equal(el('head-toggle').getAttribute('aria-pressed'),'false');el('head-toggle').onclick();
  el('year-tabs').querySelector('[data-year="0"]').onclick();assert.equal(el('editing-year').textContent,'YEAR 1');

  el('bore-count').value='4';
  const before=requests.length;await el('train').onclick();
  assert.equal(requests.length,before);assert.match(el('activity').textContent,/Create \/ resize/);
  el('year-count').value='1';el('create-plan').onclick();
  for(let i=0;i<100&&el('evaluate').disabled;i++)await delay(100);
  assert.equal(el('bore-rows').querySelectorAll('input').length,4);
  assert.match(el('activity').textContent,/Plan evaluated/);
  const expectedVolume=[...el('bore-rows').querySelectorAll('input')].reduce((sum,e)=>sum+Number(e.value)*365,0);
  el('playback-speed').value='50';
  const playing=el('simulate').onclick();
  for(let i=0;i<100&&Number(el('simulation-progress').value)===0;i++)await delay(25);
  el('pause').onclick();await playing;
  const paused=Number(el('simulation-progress').value);
  assert.ok(paused>0&&paused<365);
  assert.equal(el('simulate').textContent,'Resume simulation');
  await el('simulate').onclick();
  assert.equal(Number(el('simulation-progress').value),365);
  assert.equal(el('level-values').querySelectorAll('tr').length,13);
  assert.equal(el('stat-volume').textContent,Math.round(expectedVolume).toLocaleString());
  assert.match(el('stat-period').textContent,/Through day 365/);
  for(const input of el('bore-rows').querySelectorAll('input')){input.value='0';input.onchange();}
  el('episodes').value='1';
  await el('train').onclick();assert.match(el('activity').textContent,/No feasible pumping schedule/);
  assert.equal(requests.filter(p=>p==='/api/portable/learn/start').length,0);
  el('conductivity').value='0.1';el('conductivity').dispatchEvent(new w.Event('change'));
  await el('train').onclick();
  assert.equal(el('episode-number').textContent,'1');assert.ok(Number(el('updates').textContent)>0);assert.equal(Number(el('neural-updates').textContent),Number(el('updates').textContent));assert.ok(el('exploration-meter').value>0);
  await el('train').onclick();
  assert.match(el('level-compliance').textContent,/Best training plan/);
  assert.equal(el('episode-number').textContent,'2');
  assert.equal(requests.filter(p=>p==='/api/portable/learn/start').length,1);
  // Continuous training must exceed a one-episode batch and honour Pause.
  el('continuous-training').checked=true;
  const originalFetch=w.fetch;let completed=0;
  w.fetch=async(path,options)=>{const response=await originalFetch(path,options);
    if(path==='/api/portable/learn'&&JSON.parse(options.body).operation==='episode'&&++completed===2)el('pause').onclick();
    return response;};
  await el('train').onclick();
  assert.equal(completed,2);assert.equal(el('episode-number').textContent,'4');
  assert.match(el('activity').textContent,/Training paused/);
  w.fetch=originalFetch;el('continuous-training').checked=false;
  // Editing a bore invalidates this plan's policy and clears learning telemetry.
  const bore=el('bore-0');bore.value='250';bore.onchange();
  assert.equal(el('episode-number').textContent,'0');
  assert.equal(el('run-learned'),null);
  await el('all-off').onclick();assert.ok([...el('bore-rows').querySelectorAll('input')].every(e=>Number(e.value)===0));
  assert.equal(el('stat-volume').textContent,'0');assert.equal(el('stat-cost').textContent,'A$0');
  el('initial-rate').value='500';await el('uniform-start').onclick();
  const b=el('bore-0');b.value='1000';b.onchange();await el('equalise').onclick();
  assert.ok([...el('bore-rows').querySelectorAll('input')].every(e=>Number(e.value)===625));
  await el('evaluate').onclick();
  const ratesBefore=[...el('bore-rows').querySelectorAll('input')].map(e=>e.value);
  await el('benchmark').onclick();assert.match(el('benchmark-result').textContent,/LP/);
  assert.deepEqual([...el('bore-rows').querySelectorAll('input')].map(e=>e.value),ratesBefore);
  await el('fit-target').onclick();assert.match(el('activity').textContent,/Target-fit pumping applied/);
  await el('export').onclick();const download=JSON.parse(await exported.text());
  assert.ok(download.result.statistics);assert.equal(download.result.statistics.pumped_volume_m3,download.result.total_volume);
  // Slow/error responses must show progress immediately, prevent duplicate actions,
  // leave Pause disabled for a one-off evaluation and release all controls on error.
  const realFetch=w.fetch;let finish;w.fetch=()=>new Promise(resolve=>{finish=resolve;});
  const evaluating=el('evaluate').onclick();assert.equal(el('request-status').hidden,false);assert.equal(el('pause').disabled,true);
  assert.equal(el('fit-target').disabled,true);await el('benchmark').onclick();
  finish(new Response('',{status:502}));await evaluating;
  assert.match(el('activity').textContent,/HTTP 502/);assert.equal(el('request-status').hidden,true);assert.equal(el('evaluate').disabled,false);
  w.fetch=realFetch;
  assert.deepEqual([...w.document.querySelectorAll('button[id]')].map(e=>e.id).filter(id=>!clicked.has(id)),[]);

 }finally{dom?.window.close();child.kill('SIGTERM');await new Promise(resolve=>child.exitCode!==null?resolve():child.once('exit',resolve));}
});
