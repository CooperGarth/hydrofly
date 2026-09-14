// Decorative companion. Reward cues reflect returned episode rewards, never
// invented training events or changes to the groundwater/learning algorithms.
export function createFlyCompanion(host) {
  const win = host.ownerDocument.defaultView;
  host.innerHTML = `<div class="panel-heading"><span>FRUIT FLY / CONTROL ROOM</span><b class="pet-state">BUZZING</b></div>
  <svg class="fly-room" viewBox="0 0 360 220" role="img" aria-label="Animated fruit fly at its dewatering computer">
    <defs><radialGradient id="pet-body"><stop stop-color="#dc9b52"/><stop offset="1" stop-color="#74432e"/></radialGradient><linearGradient id="pet-glass" x2="0" y2="1"><stop stop-color="#284f48"/><stop offset="1" stop-color="#102b28"/></linearGradient></defs>
    <rect x="10" y="10" width="340" height="199" rx="16" fill="#152f29"/>
    <path d="M20 186H340M45 198H315" stroke="#426456" opacity=".5"/>
    <g class="pet-computer"><path d="M120 163H325V178H120zM135 178V202M309 178V202" fill="#5c7554" stroke="#86946b" stroke-width="3"/>
    <rect x="224" y="65" width="89" height="66" rx="5" fill="#0a201c" stroke="#849575" stroke-width="4"/><rect x="231" y="72" width="75" height="51" fill="url(#pet-glass)"/>
    <path d="M238 84h18v7h16v7h25M238 92q16 4 27 11t33 8" fill="none" stroke="#9dc2a3" stroke-width="2"/>
    <path d="M267 132v20m-13 0h27" stroke="#849575" stroke-width="5"/>
    <path d="M179 151h62l10 10h-81z" fill="#a6b294"/><path d="M185 154h51m-56 4h62" stroke="#3f5b4d" stroke-width="2"/>
    <g class="pet-cursor"><path d="M239 117h9" stroke="#dbef9d" stroke-width="2"/></g></g>
    <g class="pet-fly"><ellipse cx="165" cy="147" rx="39" ry="8" fill="#071c18" opacity=".3"/>
      <g class="pet-wing wing-back"><ellipse cx="147" cy="105" rx="32" ry="12" transform="rotate(-35 147 105)" fill="#d1ece2" opacity=".65" stroke="#eff6d9"/></g>
      <ellipse cx="155" cy="127" rx="30" ry="20" transform="rotate(-18 155 127)" fill="url(#pet-body)"/>
      <path d="M137 112q-1 13 11 30m0-34q-1 13 11 31" fill="none" stroke="#593f2b" stroke-width="3"/>
      <g class="pet-wing wing-front"><ellipse cx="163" cy="102" rx="32" ry="12" transform="rotate(-23 163 102)" fill="#e0f0dd" opacity=".8" stroke="#f2f5df"/></g>
      <circle cx="185" cy="117" r="19" fill="#876244"/><ellipse cx="195" cy="113" rx="10" ry="14" fill="#c6593e"/><ellipse cx="198" cy="109" rx="3" ry="5" fill="#f3ad73"/>
      <path d="M181 101l-6-12m14 11 4-13" stroke="#bcc3a0" stroke-width="2"/>
      <path class="pet-leg leg-one" d="M178 132l15 13 20 10" fill="none" stroke="#c3ba8a" stroke-width="3"/>
      <path class="pet-leg leg-two" d="M168 138l14 14 21 6" fill="none" stroke="#dacda0" stroke-width="3"/>
      <path d="M147 142l-10 14m23-13-5 16" stroke="#b0a67d" stroke-width="2"/>
      <ellipse class="pet-mouth" cx="203" cy="125" rx="3" ry="2" fill="#38271e"/>
      <g class="pet-soot" fill="#292f29"><ellipse cx="155" cy="127" rx="29" ry="19"/><circle cx="185" cy="117" r="18"/><path d="M132 110l-9-9 13 3m24-3 1-12 7 13m16-5 8-9-2 14"/></g>
      <g class="pet-smoke" fill="#b9b9a5" opacity="0"><circle cx="156" cy="100" r="9"/><circle cx="170" cy="86" r="12"/><circle cx="158" cy="71" r="10"/></g>
      <g class="pet-crumbs" fill="#edb95d"><circle cx="207" cy="133" r="2"/><circle cx="199" cy="139" r="1.5"/><circle cx="214" cy="143" r="2"/></g>
      <g class="pet-sweat" fill="#80c9c8"><path d="M211 98q-8 12 0 12t0-12"/><path d="M219 119q-6 10 0 10t0-10"/></g>
    </g>
    <g class="pet-food"><path d="M72 146q-12 17 5 24h17q14-13 0-24z" fill="#e6ad4f"/><path d="M82 146v-9q12-8 17-2-8 9-17 6" fill="#8bb66e"/><g class="pet-bites" fill="#152f29"><circle cx="97" cy="149" r="5"/><circle cx="94" cy="158" r="5"/></g><text x="55" y="131" fill="#d9eaa1" font-size="12">+ reward</text></g>
    <g class="pet-zap" fill="none" stroke="#e6c66c" stroke-width="3"><path d="M107 86l-12 20 17-4-11 24M224 92l-10 18 16-4-12 24"/></g>
  </svg><p class="pet-caption" aria-live="polite">Off duty. Inspecting the airspace.</p><small class="pet-note">Food / zap = positive / negative episode reward.</small>`;
  let mode='idle', effect=null, timer;
  const state=host.querySelector('.pet-state'),caption=host.querySelector('.pet-caption');
  const paint=()=>{host.dataset.mood=effect||mode;state.textContent=effect==='fed'?'SNACK TIME':effect==='zapped'?'ZAPPED':mode==='typing'?'WORKING':'BUZZING';};
  host.dataset.gesture='0';paint();
  // One uninterrupted render clock. Phases change destinations, never replace
  // frames or restart a CSS animation. Motion continues during awaited API calls.
  host.classList.add('live-animated');
  const fly=host.querySelector('.pet-fly'),wings=[...host.querySelectorAll('.pet-wing')],legs=[...host.querySelectorAll('.pet-leg')];
  const food=host.querySelector('.pet-food'),zap=host.querySelector('.pet-zap'),sweat=host.querySelector('.pet-sweat');
  const soot=host.querySelector('.pet-soot'),smoke=host.querySelector('.pet-smoke'),crumbs=host.querySelector('.pet-crumbs'),mouth=host.querySelector('.pet-mouth'),bites=host.querySelector('.pet-bites');
  let effectStart=0;
  const reduced=win.matchMedia?.('(prefers-reduced-motion: reduce)');
  let frame,previous=null,elapsed=0,x=0,y=0,angle=0,disposed=false;
  let drift=0,nextDrift=0;
  const tick=now=>{
    if(disposed)return;
    const dt=previous===null?0:Math.min((now-previous)/1000,.05);previous=now;elapsed+=dt;
    if(elapsed>=nextDrift){drift=Math.random()*Math.PI*2;nextDrift=elapsed+5+Math.random()*3;}
    const t=elapsed,quiet=!!reduced?.matches,mood=effect||mode,age=t-effectStart;
    let tx=0,ty=0,ta=0;
    if(mood==='idle'){
      tx=quiet?2*Math.sin(t):-25+62*Math.sin(t*.75)+9*Math.sin(t*1.9+drift);
      ty=quiet?-2:-29-19*Math.sin(t*.95)+6*Math.sin(t*2.2);
      ta=quiet?0:8*Math.cos(t*.75);
    }else if(mood==='typing'){
      tx=(quiet?.3:1.5)*Math.sin(t*12);ty=-1-Math.abs(Math.sin(t*6))*(quiet?.5:2);
      // Occasional continuous head/body fidgets, blended into the typing pose.
      ta=quiet?0:Math.sin(t*2.3+drift)*2.5;
    }else if(mood==='fed'){tx=quiet?-2:-40;ty=quiet?0:2;ta=quiet?0:-4+2*Math.sin(t*12);}
    else {const shock=age<.65;tx=(quiet?.4:shock?7:1)*Math.sin(t*27);ty=quiet?0:shock?-15:-4;ta=quiet?0:shock?18*Math.sin(t*23):14*Math.exp(-Math.max(0,age-.65));}
    const blend=1-Math.exp(-dt*7);x+=(tx-x)*blend;y+=(ty-y)*blend;angle+=(ta-angle)*blend;
    fly.style.transform=`translate(${x}px,${y}px) rotate(${angle}deg)`;
    wings.forEach((wing,i)=>{wing.style.transform=`scaleY(${quiet?.9:.65+.3*Math.sin(t*55+i)}) rotate(${quiet?Math.sin(t*4):7*Math.sin(t*55+i)}deg)`;});
    legs.forEach((leg,i)=>{leg.style.transform=`rotate(${mode==='typing'&&!effect?(quiet?2:11)*Math.sin(t*32+i*Math.PI):2*Math.sin(t*5+i)}deg)`;});
    food.style.opacity=mood==='fed'?String(Math.min(age*3,1)):'0';food.style.transform=`translate(${mood==='fed'?(quiet?108:70)+2*Math.sin(t*12):0}px,${mood==='fed'?-20+Math.sin(t*12):0}px)`;
    mouth.setAttribute('ry',String(mood==='fed'?2+1.5*Math.abs(Math.sin(t*14)):2));
    bites.style.opacity=mood==='fed'&&age>1.2?'1':'0';
    crumbs.style.opacity=mood==='fed'&&age>.6?'.9':'0';crumbs.style.transform=`translate(${3*Math.sin(t*9)}px,${(t*30)%18}px)`;
    soot.style.opacity=mood==='zapped'?String(Math.max(0,Math.min((age-.2)*3,1,(3.8-age)/1.2))):'0';
    smoke.style.opacity=mood==='zapped'&&age>.4?String(Math.max(0,.7*(1-age/4))):'0';
    smoke.style.transform=`translate(${4*Math.sin(t*3)}px,${-Math.min(age*9,30)}px) scale(${1+Math.min(age,4)*.06})`;
    zap.style.opacity=mood==='zapped'&&age<.65?'1':'0';zap.style.strokeDashoffset=String(-t*30);
    sweat.style.opacity=mood==='typing'||mood==='zapped'?'.8':'0';
    host.querySelector('.pet-cursor').style.opacity=String(.55+.45*Math.sin(t*5));
    frame=win.requestAnimationFrame(tick);
  };
  frame=win.requestAnimationFrame(tick);
  return {
    setPhase(value,learning=false){mode=value==='idle'?'idle':'typing';if(!effect)caption.textContent=mode==='idle'?'Off duty. Inspecting the airspace.':learning?'Training. Typing furiously; occasionally panicking.':'Checking the model. Please hold the snacks.';paint();},
    reward(value){if(!Number.isFinite(value)||Math.abs(value)<=1e-8)return;win.clearTimeout(timer);effectStart=elapsed;effect=value>0?'fed':'zapped';caption.textContent=value>0?`Positive episode reward (${value.toFixed(3)}). Fruit earned!`:`Negative episode reward (${value.toFixed(3)}). Cartoon zap!`;paint();timer=win.setTimeout(()=>{effect=null;this.setPhase(mode);},4000);},
    reset(){win.clearTimeout(timer);effect=null;this.setPhase('idle');},
    dispose(){disposed=true;win.cancelAnimationFrame(frame);win.clearTimeout(timer);}
  };
}
