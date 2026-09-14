import * as THREE from 'three';
// An original, deliberately oversized control station in the toy mine world.
// Animation reflects software state, never unobserved biological activity.
export function createFlyConsole(scene){
 const station=new THREE.Group();station.position.set(1900,2250,1600);station.rotation.y=-.35;scene.add(station);
 const mat=(color,opacity=1)=>new THREE.MeshStandardMaterial({color,roughness:.7,transparent:opacity<1,opacity,side:THREE.DoubleSide});
 function box(x,y,z,color,px,py,pz,parent=station){const o=new THREE.Mesh(new THREE.BoxGeometry(x,y,z),mat(color));o.position.set(px,py,pz);parent.add(o);return o;}
 function ball(x,y,z,color,px,py,pz,parent=station,opacity=1){const o=new THREE.Mesh(new THREE.SphereGeometry(1,16,10),mat(color,opacity));o.scale.set(x,y,z);o.position.set(px,py,pz);parent.add(o);return o;}
 box(950,35,580,0x526960,0,0,0);for(const x of [-400,400])for(const z of [-220,220])box(25,200,25,0x374b47,x,-115,z);
 const screen=box(365,220,30,0x152b32,-130,200,-170);box(25,65,25,0x648374,-130,65,-170);box(130,12,75,0x789886,-130,35,-170);
 const canvas=document.createElement('canvas');canvas.width=512;canvas.height=256;const ctx=canvas.getContext('2d'),texture=new THREE.CanvasTexture(canvas);
 const display=new THREE.Mesh(new THREE.PlaneGeometry(330,185),new THREE.MeshBasicMaterial({map:texture}));display.position.set(-130,200,-153);station.add(display);
 // Both the desk monitor and background display share the model-derived chart.
 box(1040,560,35,0x263f35,0,590,-430);
 const wallDisplay=new THREE.Mesh(new THREE.PlaneGeometry(990,515),new THREE.MeshBasicMaterial({map:texture}));wallDisplay.position.set(0,590,-410);station.add(wallDisplay);
 let model=null,message='Ready for your mine plan';
 function redraw(){
  ctx.fillStyle='#102b24';ctx.fillRect(0,0,512,256);ctx.fillStyle='#d1e3b5';ctx.font='13px monospace';ctx.fillText('WATER LEVEL / BENCH TARGET',15,21);
  if(model){
   const rows=model.years,points=model.timeline.map(p=>({t:p.day/365,h:p.head,target:p.target}));
   const values=[model.initial_floor,model.initial_floor-5,...points.map(p=>p.h),...rows.flatMap(r=>[r.floor,r.target])],lo=Math.min(...values)-3,hi=Math.max(...values)+3;
   const x=t=>48+t/rows.length*445,y=h=>191-(h-lo)/(hi-lo)*145;
   ctx.font='10px monospace';ctx.fillStyle='#a5bea2';ctx.fillText('m AHD',3,40);
   for(let i=0;i<=3;i++){const h=lo+(hi-lo)*i/3;ctx.strokeStyle='#355547';ctx.beginPath();ctx.moveTo(48,y(h));ctx.lineTo(493,y(h));ctx.stroke();ctx.fillText(h.toFixed(0),4,y(h)+3);}
   for(const [key,color,dash]of [['floor','#d6b78d',[]],['target','#e4a06f',[5,3]]]){ctx.strokeStyle=color;ctx.lineWidth=2;ctx.setLineDash(dash);ctx.beginPath();ctx.moveTo(x(0),y(model.initial_floor-(key==='target'?5:0)));rows.forEach((r,i)=>{ctx.lineTo(x(i+1),y(i?rows[i-1][key]:model.initial_floor-(key==='target'?5:0)));ctx.lineTo(x(i+1),y(r[key]));});ctx.stroke();}
   ctx.setLineDash([]);ctx.strokeStyle='#76d5de';ctx.beginPath();points.forEach((p,i)=>i?ctx.lineTo(x(p.t),y(p.h)):ctx.moveTo(x(p.t),y(p.h)));ctx.stroke();
   points.forEach(p=>{ctx.fillStyle=p.h>p.target+1e-5?'#f39a73':'#76d5de';ctx.beginPath();ctx.arc(x(p.t),y(p.h),2.5,0,Math.PI*2);ctx.fill();});
   ctx.fillStyle='#adc6a7';for(let i=0;i<=rows.length;i++)ctx.fillText('Y'+i,x(i)-8,207);
   ctx.fillStyle='#76d5de';ctx.fillText('HEAD',55,232);ctx.fillStyle='#d6b78d';ctx.fillText('FLOOR',120,232);ctx.fillStyle='#e4a06f';ctx.fillText('FLOOR - 5m',195,232);
  }else{ctx.fillText('Waiting for Python model results',30,120);}
  ctx.fillStyle='#c2d5ad';ctx.font='10px monospace';ctx.fillText(message.slice(0,77),15,250);texture.needsUpdate=true;
 }
 function text(value){message=value;redraw();}

 const keyboard=box(320,12,105,0x253c40,-130,28,65);for(let j=0;j<4;j++)for(let i=0;i<12;i++)box(18,5,15,0x8ba596,-270+i*25,37,30+j*22);
 box(200,55,180,0x697764,300,45,20);const lever=new THREE.Group();lever.position.set(300,74,20);station.add(lever);box(12,120,12,0xb0c5ac,0,60,0,lever);ball(28,23,28,0xe1ae6b,0,125,0,lever);
 for(let i=0;i<4;i++)ball(8,5,8,0x96dba5,245+i*35,76,80);
 let phase='idle',arrive=null;const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
 text('Ready for your mine plan');
 return {position:station.position,
  updateModel(result){model=result;redraw();},
  setActivity(value,message){phase=value;text(message);},
  operate(message,cancelled){this.setActivity('pulling',message);return new Promise(resolve=>{arrive={resolve,cancelled,elapsed:0};});},
  frame(now,dt){
    lever.rotation.x=phase==='pulling'&&!reduced?Math.sin(now*.004)*.4:0;
    if(arrive){arrive.elapsed+=dt;if(arrive.cancelled()){arrive.resolve(false);arrive=null;this.setActivity('idle','Paused before pump action');}else if(arrive.elapsed>(reduced?0:.8)){arrive.resolve(true);arrive=null;}}
  }};
}
