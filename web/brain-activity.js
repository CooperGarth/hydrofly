// An interactive software-controller inspector, not a biological neural map.
export function createBrainActivity(windowElement){
 const doc=windowElement.ownerDocument,win=doc.defaultView;
 const overlay=doc.createElement('div');overlay.className='brain-signals';overlay.setAttribute('aria-hidden','true');
 overlay.innerHTML='<i data-region="sense"></i><i data-region="action"></i><i data-region="update"></i>';
 windowElement.append(overlay);
 const inspector=doc.createElement('div');inspector.className='brain-inspector';
 inspector.innerHTML='<div class="brain-tabs" role="group" aria-label="Inspect controller"><button type="button" data-inspect="sense" aria-pressed="true">Observe</button><button type="button" data-inspect="action" aria-pressed="false">Decide</button><button type="button" data-inspect="update" aria-pressed="false">Learn</button></div><p class="brain-live" role="status">Idle · waiting for a model result.</p><p class="brain-explanation"></p>';
 windowElement.parentElement.append(inspector);
 let selection='sense',model=null,metrics=null,shape=null,pending=false,timer;
 const live=inspector.querySelector('.brain-live'),detail=inspector.querySelector('.brain-explanation');
 function actionLabel(action){
  if(!shape)return 'No action yet';const n=shape.bores*shape.years;
  if(action===2*n)return 'Stop this episode';
  const index=action%n;return `${action<n?'Increase':'Decrease'} bore ${index%shape.bores+1}, year ${Math.floor(index/shape.bores)+1}`;
 }
 function render(){
  windowElement.dataset.inspect=selection;
  for(const b of inspector.querySelectorAll('button'))b.setAttribute('aria-pressed',String(b.dataset.inspect===selection));
  if(selection==='sense')detail.textContent=model?`Observes the complete pumping history and modelled heads at pit controls and bores. Displayed best plan: ${model.feasible?'sampled pit targets met':'pit target exceedance'}; ${model.confined_valid?'confined assumption valid':'outside confined assumption'}. This is the retained plan, not a live view of each trial.`:'Observes the complete pumping schedule, analytical groundwater heads and pit targets. Evaluate a plan to inspect its result.';
  if(selection==='action'){
   detail.textContent=metrics?`Last completed episode: ${actionLabel(metrics.last_action)}. ${metrics.guided_actions} teacher-guided and ${metrics.exploratory_actions} exploratory actions across ${metrics.moves} trials. Exploration ε = ${metrics.epsilon.toFixed(3)}. `:'Chooses a bore-year rate increase, decrease or stop. Decisions combine teacher guidance, exploration and learned action values. Train to inspect actual decisions.';
   if(metrics?.last_action_values?.length){const top=metrics.last_action_values.map((value,action)=>({value,action})).sort((a,b)=>b.value-a.value).slice(0,3);detail.textContent+='Highest raw Q estimates at the last state (before action constraints): '+top.map(x=>`${actionLabel(x.action)}: ${x.value.toFixed(3)}`).join('; ')+'.';}
  }
  if(selection==='update')detail.textContent=metrics?`Episode ${metrics.episode}: ${metrics.updates} cumulative Q updates, ${metrics.parameters} shared weights. Reward ${metrics.reward.toFixed(4)}; mean |TD error| ${metrics.td_error.toFixed(4)}. TD error measures prediction mismatch, not groundwater error. ${pending?'Next episode is still computing; these are the last completed results.':''}`:'Learning updates seven shared action-value weights from measured rewards. No episode has completed yet; the illustration is not a simulated fly connectome.';
 }
 for(const b of inspector.querySelectorAll('button'))b.onclick=()=>{selection=b.dataset.inspect;render();};
 render();
 return {
  flash(kind='sense'){windowElement.dataset.event=kind;win.clearTimeout(timer);timer=win.setTimeout(()=>delete windowElement.dataset.event,1600);},
  setPhase(value,learning=false){pending=value!=='idle';windowElement.dataset.processing=String(pending);live.textContent=pending?(learning?'Episode computing · telemetry updates when it completes.':'Evaluating model · awaiting a result.'):(metrics?`Latest completed episode ${metrics.episode} · ${metrics.updates} Q updates.`:'Idle · inspect the controller below.');render();},
  setModel(result){model=result;render();},
  update(record,dimensions){metrics=record;shape=dimensions;live.textContent=`Episode ${record.episode} received · reward ${record.reward.toFixed(4)}.`;render();},
  reset(){metrics=null;shape=null;model=null;pending=false;windowElement.dataset.processing='false';delete windowElement.dataset.event;live.textContent='Plan changed · no learning for this configuration yet.';render();},
  dispose(){win.clearTimeout(timer);}
 };
}
