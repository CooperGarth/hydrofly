import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';

// All hydraulic elevations enter through update(result). This module contains
// geometry and contours only; it cannot compute a groundwater response.
export function createScene(container, config){
  const scene=new THREE.Scene();
  const renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});
  renderer.setPixelRatio(Math.min(devicePixelRatio,2));container.append(renderer.domElement);
  renderer.outputColorSpace=THREE.SRGBColorSpace;
  const camera=new THREE.PerspectiveCamera(39,1,1,12000);
  camera.position.set(1450,1500,1700);
  const controls=new OrbitControls(camera,renderer.domElement);
  controls.target.set(0,130,0);controls.enableDamping=true;controls.minDistance=800;controls.maxDistance=4200;controls.maxPolarAngle=Math.PI*.49;
  scene.add(new THREE.HemisphereLight(0xe7fff3,0x26372c,2.7));
  const light=new THREE.DirectionalLight(0xffdfb0,3);light.position.set(-800,1600,600);scene.add(light);
  const group=new THREE.Group();scene.add(group);
  const y=h=>(h-config.pit_floor)*4;
  const size=config.extent/650; group.scale.setScalar(1/size);
  const mat=(color,opacity=1)=>new THREE.MeshStandardMaterial({color,roughness:.9,transparent:opacity<1,opacity,side:THREE.DoubleSide,depthWrite:opacity===1});
  function box(w,h,d,x,yy,z,color,opacity=1){const m=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),mat(color,opacity));m.position.set(x,yy,z);group.add(m);return m;}
  function line(points,color,opacity=1){const g=new THREE.BufferGeometry().setFromPoints(points.map(p=>new THREE.Vector3(...p)));const m=new THREE.Line(g,new THREE.LineBasicMaterial({color,transparent:opacity<1,opacity}));group.add(m);return m;}
  function label(text,pos,color='#d4e6d8',size=95){const c=document.createElement('canvas');c.width=512;c.height=90;const ctx=c.getContext('2d');ctx.font='500 31px monospace';ctx.fillStyle=color;ctx.textAlign='center';ctx.fillText(text,256,54);const sprite=new THREE.Sprite(new THREE.SpriteMaterial({map:new THREE.CanvasTexture(c),depthTest:false,transparent:true}));sprite.position.set(...pos);sprite.scale.set(size,size*90/512,1);group.add(sprite);return sprite;}
  // Actual aquifer elevation interval (-80,0 m initially). The upper confining
  // interval is open in this illustrative cutaway so pressure heads remain visible.
  let strata=[]; const wellMeshes=[],wellLights=[];
  function setThickness(thickness){wellMeshes.forEach(tube=>{tube.geometry.dispose();tube.geometry=new THREE.CylinderGeometry(3*size,3*size,(config.crest-config.aquifer_roof+thickness)*4,8);tube.position.y=y((config.crest+config.aquifer_roof-thickness)/2);});strata.forEach(m=>{group.remove(m);m.geometry.dispose();m.material.dispose();});strata=[];for(let i=0;i<4;i++){const h=thickness/4;strata.push(box(config.extent*2,h*4-2,config.extent*2,0,y(config.aquifer_roof-h*(i+.5)),0,[0x2c4b45,0x35574d,0x2b4842,0x244039][i],.43));}}
  setThickness(config.defaults.thickness);
  label('CONFINED AQUIFER',[0,y(config.aquifer_roof)-90,config.extent],'#83a99a',240*size);
  label('PIEZOMETRIC HEAD ≠ WATER TABLE',[0,y(config.initial_head)+100,-config.extent],'#aad9ca',430*size);
  // Low-poly pit terraces. Elliptical pit floor coincides with the control ring.
  const n=64;
  function ring(rx,rz,h){return Array.from({length:n+1},(_,i)=>{const a=i/n*Math.PI*2;return [rx*Math.cos(a),y(h),rz*Math.sin(a)];});}
  function band(inner,outer,color){const verts=[],ix=[];for(let i=0;i<=n;i++)verts.push(...inner[i],...outer[i]);for(let i=0;i<n;i++){const k=i*2;ix.push(k,k+1,k+2,k+1,k+3,k+2);}const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.Float32BufferAttribute(verts,3));geo.setIndex(ix);geo.computeVertexNormals();group.add(new THREE.Mesh(geo,mat(color)));}
  const dr=(config.rim_rx-config.floor_rx)/5,dz=(config.rim_ry-config.floor_ry)/5,dh=(config.crest-config.pit_floor)/5;
  for(let i=0;i<5;i++){const h=config.pit_floor+i*dh,rx=config.floor_rx+i*dr,rz=config.floor_ry+i*dz;band(ring(rx,rz,h),ring(rx+dr*.65,rz+dz*.65,h),[0x927953,0x9f835c,0xad9165,0xbaa273,0xc3ab7e][i]);band(ring(rx+dr*.65,rz+dz*.65,h),ring(rx+dr,rz+dz,h+dh),0x6c614a);line(ring(rx,rz,h+.2),0xe7c993,.3);}
  const floor=new THREE.Mesh(new THREE.CircleGeometry(1,64),mat(0x786b50));floor.rotation.x=-Math.PI/2;floor.scale.set(config.floor_rx,config.floor_ry,1);floor.position.y=y(config.pit_floor);group.add(floor);
  line(ring(config.floor_rx+6,config.floor_ry+6,config.target),0xf4a56e);
  label(`TARGET ${config.target} m`,[0,y(config.target)-12,config.floor_ry+50],'#f4a56e',190*size);
  label(`PIT FLOOR ${config.pit_floor} m`,[0,y(config.pit_floor)+7,0],'#eee0b5',220*size);
  config.wells.forEach(([x,z],i)=>{
    const tube=new THREE.Mesh(new THREE.CylinderGeometry(3*size,3*size,(config.crest-config.aquifer_roof+config.defaults.thickness)*4,8),mat(0xb8d5c9,.85));tube.position.set(x,y((config.crest+config.aquifer_roof-config.defaults.thickness)/2),z);group.add(tube);wellMeshes.push(tube);
    const collar=new THREE.Mesh(new THREE.CylinderGeometry(9*size,12*size,9*size,12),mat(0xdef4d9));collar.position.set(x,y(config.crest)+5,z);group.add(collar);
    const bulb=new THREE.Mesh(new THREE.SphereGeometry(6*size,10,8),new THREE.MeshBasicMaterial({color:0xa3dec8}));bulb.position.set(x,y(config.crest)+22,z);group.add(bulb);wellLights.push(bulb);
    label(`W${String(i+1).padStart(2,'0')}`,[x,y(config.crest)+44,z],'#c5e6d6',75*size);
  });
  const fly=new THREE.Group();group.add(fly);
  function ellipsoid(a,b,c,color,x=0,yy=0,z=0){const m=new THREE.Mesh(new THREE.SphereGeometry(1,16,12),mat(color));m.scale.set(a,b,c);m.position.set(x,yy,z);fly.add(m);return m;}
  ellipsoid(10,9,17,0xeea35c);ellipsoid(9,8,9,0x2b3027,0,4,-14);ellipsoid(4,5,4,0xed714a,-6,7,-19);ellipsoid(4,5,4,0xed714a,6,7,-19);
  const wings=[ellipsoid(16,1,8,0xd6f7ed,-15,10,0),ellipsoid(16,1,8,0xd6f7ed,15,10,0)];wings.forEach(w=>{w.material.transparent=true;w.material.opacity=.72;});
  for(let i=0;i<6;i++){const leg=new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3((i%2?1:-1)*6,0,(Math.floor(i/2)-1)*8),new THREE.Vector3((i%2?1:-1)*17,-14,(Math.floor(i/2)-1)*13)]),new THREE.LineBasicMaterial({color:0x21271f}));fly.add(leg);}
  fly.scale.setScalar(size);fly.position.set(config.wells[0][0],y(config.crest)+60*size,config.wells[0][1]);fly.visible=false;let flyTarget=fly.position.clone(),journey=null;
  let surface=null,contours=null,surfaceVisible=true;
  function colour(h){const t=THREE.MathUtils.clamp((h-(config.target-25))/(config.initial_head-config.target+25),0,1);return new THREE.Color().set(t<.5?0xdfb562:0x72ceb9).lerp(new THREE.Color(t<.5?0x72ceb9:0x31537e),t<.5?t*2:(t-.5)*2);}
  function update(result){
    if(!result.surface)return;
    if(surface){group.remove(surface);surface.geometry.dispose();surface.material.dispose();}
    if(contours){group.remove(contours);contours.geometry.dispose();contours.material.dispose();}
    const axis=result.axis,h=result.surface,N=axis.length,positions=[],colors=[],indices=[];
    for(let j=0;j<N;j++)for(let i=0;i<N;i++){positions.push(axis[i],y(h[j][i]),axis[j]);const c=colour(h[j][i]);colors.push(c.r,c.g,c.b);}
    for(let j=0;j<N-1;j++)for(let i=0;i<N-1;i++){const k=j*N+i;indices.push(k,k+N,k+1,k+1,k+N,k+N+1);}
    const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));geo.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));geo.setIndex(indices);geo.computeVertexNormals();
    surface=new THREE.Mesh(geo,new THREE.MeshStandardMaterial({vertexColors:true,transparent:true,opacity:.69,side:THREE.DoubleSide,roughness:.4,metalness:.1,depthWrite:false}));surface.visible=surfaceVisible;group.add(surface);
    // Contours are linear intersections with the same model-derived triangles.
    const segments=[];for(let level=config.target-25;level<=config.initial_head;level+=2.5){for(let n=0;n<indices.length;n+=3){const crossings=[];for(let e=0;e<3;e++){const a=indices[n+e],b=indices[n+(e+1)%3],ha=positions[a*3+1]/4+config.pit_floor,hb=positions[b*3+1]/4+config.pit_floor;if((ha<level&&hb>=level)||(hb<level&&ha>=level)){const t=(level-ha)/(hb-ha);crossings.push(positions[a*3]+t*(positions[b*3]-positions[a*3]),y(level)+.5,positions[a*3+2]+t*(positions[b*3+2]-positions[a*3+2]));}}if(crossings.length===6)segments.push(...crossings);}}
    const cg=new THREE.BufferGeometry();cg.setAttribute('position',new THREE.Float32BufferAttribute(segments,3));contours=new THREE.LineSegments(cg,new THREE.LineBasicMaterial({color:0xc6ecda,transparent:true,opacity:.36}));contours.visible=surfaceVisible;group.add(contours);
    result.rates.forEach((q,i)=>{wellLights[i].material.color.set(q>1?0xa3dec8:0x536460);wellLights[i].scale.setScalar(.65+q/6000*.7);});
  }
  function resize(){const w=container.clientWidth,h=container.clientHeight;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();}
  new ResizeObserver(resize).observe(container);resize();
  let previous=performance.now();const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
  function frame(now){requestAnimationFrame(frame);const dt=Math.min((now-previous)/1000,.1);previous=now;controls.update();if(journey&&journey.cancelled()){flyTarget.copy(fly.position);journey.resolve(false);journey=null;}if(fly.visible){fly.position.lerp(flyTarget,reduced?1:1-Math.exp(-dt*3));fly.rotation.y=Math.atan2(flyTarget.x-fly.position.x,flyTarget.z-fly.position.z);if(!reduced){wings[0].rotation.z=Math.sin(now*.06)*.5;wings[1].rotation.z=-Math.sin(now*.06)*.5;}}if(journey&&fly.position.distanceTo(flyTarget)<size){fly.position.copy(flyTarget);journey.resolve(true);journey=null;}renderer.render(scene,camera);}requestAnimationFrame(frame);
  let plan=false;return {update,setThickness,setFly(active){fly.visible=active;},travelTo(i,cancelled){const [x,z]=config.wells[i];flyTarget.set(x,y(config.crest)+60*size,z);return new Promise(resolve=>{journey={resolve,cancelled};});},toggleSurface(){surfaceVisible=!surfaceVisible;if(surface)surface.visible=surfaceVisible;if(contours)contours.visible=surfaceVisible;return surfaceVisible;},togglePlan(){plan=!plan;camera.position.set(...(plan?[0,2500,.01]:[1450,1500,1700]));controls.target.set(0,130,0);controls.update();return plan;}};
}
