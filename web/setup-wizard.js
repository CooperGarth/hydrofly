// Guided setup wizard: mirrors the existing mine-plan inputs step by step,
// then applies them through the same handlers a manual edit would use.
const $=id=>document.getElementById(id);
const steps=[
 {title:'Borefield & plan length',blurb:'How many pumps will the fly operate, and how many years should the plan run?',
  fields:[{id:'bore-count',label:'Bores'},{id:'year-count',label:'Plan years'},{id:'capacity',label:'Capacity per bore · m³/day'},{id:'initial-rate',label:'Starting rate per bore · m³/day'}]},
 {title:'Bench schedule',blurb:'Set the starting pit floor and how far the bench drops at each year-end. The compliance target stays 5 m below each bench.',
  fields:[{id:'initial-floor',label:'Initial floor · m AHD'}],floors:true},
 {title:'Aquifer properties',blurb:'The groundwater setting your borefield works against. The defaults match the fitted demo scenario.',
  fields:[{id:'initial-head',label:'Initial water level · m AHD'},{id:'conductivity',label:'K · m/day'},{id:'thickness',label:'Thickness · m'},{id:'storativity',label:'Storativity'},{id:'view-extent',label:'Modelled half-width'}]},
 {title:'Goal & training',blurb:'Choose what the fly should minimise and how hard to train. Every objective must keep the water level 5 m below the bench.',
  fields:[{id:'objective',label:'Objective'},{id:'teaching-strategy',label:'Teaching strategy'},{id:'rate-step',label:'Rate step · m³/day'},{id:'episodes',label:'Episodes per batch'}]}];
let current=0;const floors=[];let fitAfter=true;
const mirror=real=>{const tag=real.tagName==='SELECT'?'select':'input';const el=document.createElement(tag);el.className='wizard-mirror';el.type=real.type||undefined;el.value=real.value;el.setAttribute('aria-label',real.closest('label')?.childNodes[0]?.textContent?.trim()||real.id);for(const a of ['min','max','step'])if(real.getAttribute(a))el.setAttribute(a,real.getAttribute(a));
 el.addEventListener('change',()=>{real.value=el.value;real.dispatchEvent(new Event('change',{bubbles:true}));});return el;};
const commit=mirror=>{const real=$(mirror.dataset.target);real.value=mirror.value;real.dispatchEvent(new Event('change',{bubbles:true}));};
function waitRows(years,ms=170000){return new Promise(resolve=>{const start=Date.now();const poll=()=>{if(document.querySelectorAll('#floor-rows input').length===years&&$('request-status').hidden)return resolve(true);if(Date.now()-start>ms)return resolve(false);setTimeout(poll,300);};poll();});}
function render(){
 const step=steps[current],body=$('wizard-body');body.replaceChildren();
 const head=document.createElement('div');head.className='wizard-head';
 head.innerHTML=`<span class="wizard-step-label">STEP ${current+1} / ${steps.length}</span><div class="wizard-dots">${steps.map((_,i)=>`<i class="${i<=current?'done':''}"></i>`).join('')}</div>`;
 const title=document.createElement('h3');title.textContent=step.title;
 const blurb=document.createElement('p');blurb.className='hint';blurb.textContent=step.blurb;
 body.append(head,title,blurb);
 const grid=document.createElement('div');grid.className='wizard-fields';body.append(grid);
 for(const f of step.fields){const real=$(f.id);const label=document.createElement('label');label.textContent=f.label;const m=mirror(real);m.dataset.target=f.id;label.append(m);grid.append(label);}
 if(step.floors){const years=Number($('year-count').value),base=Number($('initial-floor').value);
  while(floors.length<years)floors.push(base-25-8*floors.length);floors.length=years;
  const wrap=document.createElement('div');wrap.className='wizard-floors';
  wrap.innerHTML=`<div class="section-label">YEAR-END FLOOR ELEVATIONS · M AHD</div>`;
  const grid2=document.createElement('div');grid2.className='wizard-floor-grid';
  floors.forEach((v,i)=>{const label=document.createElement('label');label.textContent=`Y${i+1}`;const input=document.createElement('input');input.type='number';input.className='wizard-mirror';input.value=v;input.setAttribute('aria-label',`Year ${i+1} floor in metres AHD`);input.addEventListener('change',()=>floors[i]=Number(input.value));label.append(input);grid2.append(label);});
  wrap.append(grid2,(()=>{const p=document.createElement('p');p.className='hint';p.textContent='Defaults step the pit 25 m in year 1, then 8 m per year. Edit any year.';return p;})());body.append(wrap);}
 if(current===steps.length-1){const check=document.createElement('label');check.className='wizard-fit';check.innerHTML=`<input type="checkbox" ${fitAfter?'checked':''}/> Fit water level after setup (conventional drawdown fit — recommended first run)`;check.querySelector('input').addEventListener('change',e=>fitAfter=e.target.checked);body.append(check);}
 const nav=document.createElement('div');nav.className='wizard-nav';
 const back=document.createElement('button');back.textContent='Back';back.disabled=current===0;back.onclick=()=>{if(current>0){current--;render();}};
 const next=document.createElement('button');next.className='primary';
 if(current<steps.length-1){next.textContent='Next';next.onclick=()=>{for(const m of body.querySelectorAll('.wizard-mirror[data-target]')){const real=$(m.dataset.target);if(!real.checkValidity()){real.reportValidity();return;}}current++;render();};}
 else{next.textContent='Create plan & evaluate';next.onclick=async()=>{
   for(const m of body.querySelectorAll('.wizard-mirror[data-target]'))commit(m);
   next.disabled=true;next.textContent='Creating plan…';
   $('create-plan').click();
   const ok=await waitRows(Number($('year-count').value));
   if(!ok){next.textContent='Setup timed out — check the status message';next.disabled=false;return;}
   const rows=document.querySelectorAll('#floor-rows input');
   rows.forEach((el,i)=>{el.value=floors[i];el.dispatchEvent(new Event('change',{bubbles:true}));});
   next.textContent='Evaluating…';
   if(fitAfter){$('fit-target').click();}else{$('evaluate').click();}
   next.textContent='Done — plan is running below';nav.querySelector('.wizard-reset').hidden=false;
 };nav.append(back,next);}
 const reset=document.createElement('button');reset.className='wizard-reset';reset.hidden=true;reset.textContent='Restart wizard';reset.onclick=()=>{current=0;render();};
 nav.append(reset);body.append(nav);
}
$('setup-wizard').addEventListener('toggle',()=>{if($('setup-wizard').open)render();});
render();
