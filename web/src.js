import './style.css';
import {createScene} from './scene.js';
import {playFly} from './game-loop.js';

const $=id=>document.getElementById(id);
let flyState={},rates=Array(10).fill(0),mode='fly',busy=false,replayToken=0,scene,lastResult;
const sliders=[];
const config=await fetch('/api/config?level='+encodeURIComponent(new URLSearchParams(location.search).get('level')||'superpit')).then(r=>{if(!r.ok)throw Error('Model configuration unavailable');return r.json();}).catch(e=>{$('loading').textContent=e.message;throw e;});
for(const [key,value] of Object.entries(config.defaults)){
  if(![...$(key).options].some(o=>Number(o.value)===value))$(key).add(new Option(String(value),String(value)));
  $(key).value=String(value);
}
$('level').value=config.level;
$('target-rule').textContent=`TARGET ≤ ${config.target.toFixed(2)} m / FLOOR ${config.pit_floor.toFixed(2)} m`;
$('legend-low').textContent=`${config.target-25} m`;$('legend-high').textContent=`${config.initial_head} m`;
$('mine-reference').hidden=config.level!=='superpit';
try{scene=createScene($('scene'),config);}catch(e){$('loading').textContent='3-D graphics unavailable. Numerical controls remain usable.';console.error(e);}
function scenario(){return {level:config.level,rates:[...rates],...Object.fromEntries(['day','conductivity','thickness','storativity'].map(k=>[k,Number($(k).value)]))};}
function setBusy(value){busy=value;document.querySelectorAll('aside button,aside input,aside textarea,aside select,.parameters select,#level').forEach(el=>el.disabled=value);$('stop').disabled=false;}
async function post(path,body){const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});if(!r.ok){const error=await r.json();throw Error(typeof error.detail==='string'?error.detail:'Invalid scenario parameters');}return r.json();}
function show(result){lastResult=result;rates=[...result.rates];rates.forEach((q,i)=>{sliders[i].value=q;$(`q${i}`).textContent=Math.round(q).toLocaleString();});$('worst').textContent=result.worst_head.toFixed(2);$('total').textContent=Math.round(result.total_rate).toLocaleString();$('score').textContent=result.score<10?result.score.toFixed(3):result.score.toFixed(1);$('compliance').textContent=result.feasible?'TARGET MET':'TARGET NOT MET';$('compliance').className=result.feasible?'good':'';if(!result.confined_valid_at_samples){$('compliance').textContent='OUTSIDE CONFINED ASSUMPTION';$('compliance').className='';}$('scene-tag').textContent=`DAY ${result.day} / CONSTANT-RATE SCENARIO`;$('iteration').textContent=`ITER ${String(result.iteration??0).padStart(2,'0')}`;scene?.update(result);$('loading').hidden=true;}
function highlight(i){document.querySelectorAll('.well').forEach((el,j)=>el.classList.toggle('active',j===i));}
async function calculate(){if(busy)return;flyState={};setBusy(true);$('activity').textContent='Calculating with timflow…';$('loading').hidden=false;$('loading').textContent='Evaluating the Python groundwater model…';try{const s=scenario();const r=await post('/api/evaluate',s);scene?.setThickness(s.thickness);show(r);$('transmissivity').textContent=`T = ${s.conductivity*s.thickness} m²/day`;$('activity').textContent=r.confined_valid_at_samples?'Model updated. Rates apply from day zero.':'Head falls below the aquifer roof at sampled points: this confined scenario is invalid.';}catch(e){$('activity').textContent=e.message;$('loading').textContent='Model unavailable. Previous result retained.';}finally{setBusy(false);}}
rates.forEach((q,i)=>{const row=document.createElement('div');row.className='well';row.innerHTML=`<label for="w${i}">W${String(i+1).padStart(2,'0')}</label><input id="w${i}" type="range" min="0" max="6000" step="50" value="${q}" aria-label="Well ${i+1} pumping rate in cubic metres per day"><output id="q${i}" for="w${i}">${q.toLocaleString()}</output>`;$('wells').append(row);const input=$(`w${i}`);sliders.push(input);input.addEventListener('input',()=>{rates[i]=Number(input.value);$(`q${i}`).textContent=rates[i].toLocaleString();highlight(i);});input.addEventListener('change',calculate);});
document.querySelectorAll('[data-mode]').forEach(button=>button.addEventListener('click',()=>{mode=button.dataset.mode;document.querySelectorAll('[data-mode]').forEach(b=>b.classList.toggle('selected',b===button));$('run').hidden=mode==='manual';scene?.setFly(mode==='fly');$('strategy-panel').hidden=mode!=='fly';$('step').hidden=mode!=='fly';flyState={};$('mode-description').textContent=mode==='manual'?'You have the controls. Adjust each well and watch the head surface respond.':mode==='fly'?'Your strategy chooses the next well. The fly travels, changes one pump, evaluates the result, then decides again.':'SLSQP searches for low pumping while enforcing the target at all 25 pit control points.';$('run').textContent=mode==='fly'?'Let the fly operate ↗':'Find an efficient configuration ↗';}));
async function run(single=false){if(busy)return;setBusy(true);const token=++replayToken;const cancelled=()=>token!==replayToken;$('stop').hidden=false;
try{
  if(mode==='fly'){
    if(!scene)throw Error('The fly needs a working 3-D view to travel. Manual and Optimiser modes remain available.');
    const strategy=JSON.parse($('strategy').value);
    const request=await playFly({request:{...scenario(),strategy,state:flyState},cancelled,single,
      decide:r=>post('/api/fly/decide',r),
      travel:action=>{highlight(action.well);$('activity').textContent=`${action.reason}. Flying to W${String(action.well+1).padStart(2,'0')}: ${Math.round(action.from_rate)} → ${Math.round(action.to_rate)} m³/day.`;return scene.travelTo(action.well,cancelled);},
      act:r=>post('/api/fly/act',r),
      show:(result,reason)=>{if(result)show(result);$('activity').textContent=reason;}});
    flyState=request.state;
    if(cancelled())$('activity').textContent='Fly paused. Resume continues from the displayed pumping configuration.';
  }else{
    $('activity').textContent='Calculating the conventional optimisation benchmark…';
    const result=await post('/api/optimise',scenario());
    if(!cancelled()){show(result.frames.at(-1));$('activity').textContent=`${result.message}. Conventional benchmark: ${result.trace.length-1} iterations.`;}
  }
}catch(e){$('activity').textContent=e.message;}finally{$('stop').hidden=true;setBusy(false);}}
$('run').addEventListener('click',()=>run());$('step').addEventListener('click',()=>run(true));
$('stop').addEventListener('click',()=>{replayToken++;$('activity').textContent='Pausing the fly…';});
$('strategy').addEventListener('change',()=>{flyState={};});
$('preset').addEventListener('change',()=>{const strategy=JSON.parse($('strategy').value);strategy.search=$('preset').value;$('strategy').value=JSON.stringify(strategy,null,2);flyState={};});
$('level').addEventListener('change',()=>{location.search='?level='+$('level').value;});
$('zero').addEventListener('click',()=>{rates.fill(0);calculate();});$('equal').addEventListener('click',()=>{const average=rates.reduce((a,b)=>a+b,0)/10;rates.fill(average);calculate();});
['day','conductivity','thickness','storativity'].forEach(id=>$(id).addEventListener('change',calculate));
$('surface-button').addEventListener('click',()=>{const visible=scene?.toggleSurface();$('surface-button').setAttribute('aria-pressed',String(visible));});
$('view-button').addEventListener('click',()=>{$('view-button').textContent=scene?.togglePlan()?'3-D view':'Plan view';});
$('about-button').addEventListener('click',()=>{$('science').hidden=!$('science').hidden;if(!$('science').hidden)$('science').scrollIntoView({behavior:'smooth'});});
document.querySelector('[data-mode=fly]').click();
await calculate();
