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
 function text(message){ctx.fillStyle='#173b3b';ctx.fillRect(0,0,512,256);ctx.fillStyle='#c9e6b5';ctx.font='24px monospace';ctx.fillText('HYDRO / CONTROL',24,40);ctx.fillStyle='#82b9a6';ctx.font='18px monospace';const words=message.split(' ');let line='',y=90;for(const word of words){if((line+word).length>31){ctx.fillText(line,24,y);y+=30;line='';}line+=word+' ';}ctx.fillText(line,24,y);texture.needsUpdate=true;}
 const keyboard=box(320,12,105,0x253c40,-130,28,65);for(let j=0;j<4;j++)for(let i=0;i<12;i++)box(18,5,15,0x8ba596,-270+i*25,37,30+j*22);
 box(200,55,180,0x697764,300,45,20);const lever=new THREE.Group();lever.position.set(300,74,20);station.add(lever);box(12,120,12,0xb0c5ac,0,60,0,lever);ball(28,23,28,0xe1ae6b,0,125,0,lever);
 for(let i=0;i<4;i++)ball(8,5,8,0x96dba5,245+i*35,76,80);
 const fly=new THREE.Group();fly.position.set(-145,105,220);station.add(fly);
 ball(45,40,78,0x97653f,0,40,30,fly);ball(39,37,44,0x364740,0,52,-35,fly);ball(18,22,21,0xe08b62,-26,61,-60,fly);ball(18,22,21,0xe08b62,26,61,-60,fly);
 for(const z of [5,30,55]){const stripe=new THREE.Mesh(new THREE.TorusGeometry(37,5,6,18),mat(0x473c31));stripe.position.set(0,40,z);stripe.scale.y=.9;fly.add(stripe);}
 const wings=[ball(29,5,92,0xd3e8dc,-45,84,35,fly,.6),ball(29,5,92,0xd3e8dc,45,84,35,fly,.6)];wings[0].rotation.y=-.4;wings[1].rotation.y=.4;
 const legs=[];for(let i=0;i<6;i++){const side=i%2?1:-1,z=(Math.floor(i/2)-1)*36;const points=[new THREE.Vector3(side*24,32,z),new THREE.Vector3(side*60,10,z-25),new THREE.Vector3(side*65,-25,z-50)];const o=new THREE.Line(new THREE.BufferGeometry().setFromPoints(points),new THREE.LineBasicMaterial({color:0xc0c6a5}));fly.add(o);legs.push(o);}
 const target=fly.position.clone();let phase='idle',arrive=null;const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
 text('Ready for your mine plan');
 return {position:station.position,
  setActivity(value,message){phase=value;text(message);target.set(...(value==='pulling'?[300,110,150]:[-145,105,220]));},
  operate(message,cancelled){this.setActivity('pulling',message);return new Promise(resolve=>{arrive={resolve,cancelled,elapsed:0};});},
  frame(now,dt){fly.position.lerp(target,reduced?1:1-Math.exp(-dt*5));fly.rotation.y=phase==='pulling'?0:0;
    if(!reduced){wings.forEach((w,i)=>w.rotation.z=Math.sin(now*.055)*(i?1:-1)*.15);legs.forEach((leg,i)=>leg.rotation.x=phase==='typing'?Math.sin(now*.03+i)*.2:0);}
    lever.rotation.x=phase==='pulling'&&!reduced?Math.sin(now*.004)*.4:0;
    if(arrive){arrive.elapsed+=dt;if(arrive.cancelled()){arrive.resolve(false);arrive=null;this.setActivity('idle','Paused before pump action');}else if((reduced||fly.position.distanceTo(target)<6)&&arrive.elapsed>(reduced?0:.8)){arrive.resolve(true);arrive=null;}}
  }};
}
