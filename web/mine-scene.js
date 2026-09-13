import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {createFlyConsole} from './fly-console.js';

export function createMineScene(container){
 const scene=new THREE.Scene(),renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});
 renderer.setPixelRatio(Math.min(devicePixelRatio,2));container.append(renderer.domElement);
 const camera=new THREE.PerspectiveCamera(36,1,1,150000);camera.position.set(4700,3200,6200);
 const orbit=new OrbitControls(camera,renderer.domElement);orbit.target.set(0,450,0);orbit.enableDamping=true;orbit.minDistance=1800;orbit.maxDistance=90000;orbit.maxPolarAngle=Math.PI*.85;
 scene.add(new THREE.HemisphereLight(0xf2f4dc,0x293c47,2.7));const sun=new THREE.DirectionalLight(0xffdbab,3);sun.position.set(-3000,6000,4000);scene.add(sun);
 const consoleWorld=createFlyConsole(scene);
 const root=new THREE.Group();scene.add(root);let dynamic=new THREE.Group();root.add(dynamic);let headGroup=new THREE.Group();root.add(headGroup);let visible=true,section=false;
 const y=h=>(h+650)*2;
 const material=(color,opacity=1)=>new THREE.MeshStandardMaterial({color,roughness:.9,side:THREE.DoubleSide,transparent:opacity<1,opacity,depthWrite:opacity===1});
 const colours=[0x738a80,0x596774,0x8e776e];
 function clear(group){while(group.children.length){const o=group.children[0];group.remove(o);o.traverse(c=>{c.geometry?.dispose();if(c.material){const mats=Array.isArray(c.material)?c.material:[c.material];mats.forEach(m=>{m.map?.dispose();m.dispose();});}});}}
 function mesh(vertices,indices,color,group=dynamic,opacity=1){const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.Float32BufferAttribute(vertices,3));geo.setIndex(indices);geo.computeVertexNormals();const m=new THREE.Mesh(geo,material(color,opacity));group.add(m);return m;}
 function line(points,color,group=dynamic){const geo=new THREE.BufferGeometry().setFromPoints(points.map(p=>new THREE.Vector3(...p)));const o=new THREE.Line(geo,new THREE.LineBasicMaterial({color,transparent:true,opacity:.7}));group.add(o);return o;}
 function label(text,position,size=340,color='#c6d7b7'){const c=document.createElement('canvas');c.width=512;c.height=80;const ctx=c.getContext('2d');ctx.font='26px monospace';ctx.fillStyle=color;ctx.textAlign='center';ctx.fillText(text,256,48);const o=new THREE.Sprite(new THREE.SpriteMaterial({map:new THREE.CanvasTexture(c),transparent:true,depthTest:false}));o.scale.set(size,size*80/512,1);o.position.set(...position);dynamic.add(o);}
 // Clip cross-section polygons against dipping interpretive contacts. These are
 // geometry only and deliberately do not alter the homogeneous hydraulic model.
 function clip(poly,bound,keepGreater){const out=[];for(let i=0;i<poly.length;i++){const a=poly[i],b=poly[(i+1)%poly.length],fa=a[0]-.35*(a[1]-360)-bound,fb=b[0]-.35*(b[1]-360)-bound;const inside=keepGreater?fa>=0:fa<=0;if(inside)out.push(a);if((fa<0)!==(fb<0)){const t=fa/(fa-fb);out.push([a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])]);}}return out;}
 function polygon(poly,color,depth=0){if(poly.length<3)return;const shape=new THREE.Shape(poly.map(p=>new THREE.Vector2(p[0],y(p[1]))));const geo=depth?new THREE.ExtrudeGeometry(shape,{depth,bevelEnabled:false,steps:1}):new THREE.ShapeGeometry(shape);const o=new THREE.Mesh(geo,material(color));if(depth)o.position.z=-depth;dynamic.add(o);}
 function ring(rx,rz,h){return Array.from({length:49},(_,i)=>{const a=Math.PI+i/48*Math.PI;return [rx*Math.cos(a),y(h),rz*Math.sin(a)];});}
 function band(a,b,color){const v=[],ix=[];a.forEach((p,i)=>v.push(...p,...b[i]));for(let i=0;i<a.length-1;i++){const k=i*2;ix.push(k,k+1,k+2,k+1,k+3,k+2);}mesh(v,ix,color);}
 let lastFloor=null,lastWells=null;
 function geology(floor,wells,rates){clear(dynamic);const steps=10,dr=(1890-800)/steps,dh=(360-floor)/steps;
  const left=[[-2600,360],[-1890,360]];for(let i=steps-1;i>=0;i--){const x=-(800+i*dr),h=floor+i*dh;left.push([x-dr*.7,h+dh],[x-dr*.7,h],[x,h]);}
  const profile=[...left,[800,floor],...left.slice(0,-1).reverse().map(p=>[-p[0],p[1]]),[2600,-1100],[-2600,-1100]];
  // The cut face is at z=0; back extrusion and half-pit terraces form the cutaway.
  const cuts=[-4000,-850,900,4000];for(let i=0;i<3;i++)polygon(clip(clip(profile,cuts[i],true),cuts[i+1],false),colours[i],650);
  polygon([[-2600,360],[-1890,360],[-1920,320],[-2600,320]],0xbd9363,650);
  polygon([[1890,360],[2600,360],[2600,320],[1920,320]],0xbd9363,650);
  for(let i=0;i<steps;i++){const h=floor+i*dh,rx=800+i*dr,rz=100+i*(805-100)/steps;const dx=dr,dz=(805-100)/steps;band(ring(rx,rz,h),ring(rx+dx*.7,rz+dz*.7,h),0xa28b68);band(ring(rx+dx*.7,rz+dz*.7,h),ring(rx+dx,rz+dz,h+dh),i%3===0?0x596774:0x8c7f69);line(ring(rx,rz,h+.5),0xc9b98d);}
  const floorPoints=ring(800,100,floor),v=[0,y(floor),0,...floorPoints.flat()],ix=[];for(let i=1;i<floorPoints.length;i++)ix.push(0,i,i+1);mesh(v,ix,0x8e805f);
  // Pressure-head target extends into the open cut so it remains visible below floor.
  line([[-900,y(floor-5),35],[900,y(floor-5),35]],0xf2ba78);label(`FLOOR ${floor} m AHD`,[0,y(floor)+50,55],700);label(`TARGET ${floor-5} m`,[0,y(floor-5)-70,80],550,'#efc28d');
  label('GOLDEN MILE DOLERITE',[100,y(-800),30],1100,'#bcc9cc');label('VOLCANIC ROCKS',[-1740,y(-550),30],700);label('SEDIMENTARY ROCKS',[1760,y(-500),30],800,'#d2bcb0');
  for(const [i,[x,z]] of wells.entries()){
    // Full well locations remain visible, including the removed foreground half.
    const tube=new THREE.Mesh(new THREE.CylinderGeometry(7,7,(360+1100)*2,8),material(0xa8c7b5,.7));tube.position.set(x,(y(360)+y(-1100))/2,z);dynamic.add(tube);
    const collar=new THREE.Mesh(new THREE.CylinderGeometry(22,29,18,12),material(0xc9d7bc));collar.position.set(x,y(360)+12,z);dynamic.add(collar);
    const bulb=new THREE.Mesh(new THREE.SphereGeometry(14,10,8),new THREE.MeshBasicMaterial({color:rates[i]>0?0xaee7b6:0x485b59}));bulb.position.set(x,y(360)+48,z);dynamic.add(bulb);
    label(`B${String(i+1).padStart(2,'0')}`,[x,y(360)+110,z],250);
  }
  line([[-2600,y(-1100),650],[2600,y(-1100),650]],0x73978a);label('5.2 km', [0,y(-1100)-90,650],500);
 }
 function update(result){consoleWorld.updateModel(result);geology(result.floor,result.wells,result.rates[result.active_year]);clear(headGroup);const axis=result.axis,N=axis.length,v=[],col=[],ix=[];for(let j=0;j<N;j++)for(let i=0;i<N;i++){const h=result.surface[j][i];v.push(axis[i],y(h),axis[j]);const c=new THREE.Color(0xddb97b).lerp(new THREE.Color(0x78c5bf),THREE.MathUtils.clamp((h-result.target+25)/60,0,1));col.push(c.r,c.g,c.b);}for(let j=0;j<N-1;j++)for(let i=0;i<N-1;i++){const k=j*N+i;ix.push(k,k+N,k+1,k+1,k+N,k+N+1);}const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.Float32BufferAttribute(v,3));geo.setAttribute('color',new THREE.Float32BufferAttribute(col,3));geo.setIndex(ix);geo.computeVertexNormals();headGroup.add(new THREE.Mesh(geo,new THREE.MeshStandardMaterial({vertexColors:true,side:THREE.DoubleSide,transparent:true,opacity:.55,depthWrite:false,roughness:.4})));
  // Contours intersect triangles from the numerical mesh, not decorative cones.
  const segments=[];for(let h=result.target-20;h<=-350;h+=5){const level=y(h);for(let k=0;k<ix.length;k+=3){const crosses=[];for(let e=0;e<3;e++){const a=ix[k+e]*3,b=ix[k+(e+1)%3]*3,ha=v[a+1],hb=v[b+1];if((ha<level&&hb>=level)||(hb<level&&ha>=level)){const t=(level-ha)/(hb-ha);crosses.push(v[a]+t*(v[b]-v[a]),level+1,v[a+2]+t*(v[b+2]-v[a+2]));}}if(crosses.length===6)segments.push(...crosses);}}
  const cg=new THREE.BufferGeometry();cg.setAttribute('position',new THREE.Float32BufferAttribute(segments,3));headGroup.add(new THREE.LineSegments(cg,new THREE.LineBasicMaterial({color:0xc0e1c3,transparent:true,opacity:.45})));headGroup.visible=visible;
 }
 const resize=()=>{const w=container.clientWidth,h=container.clientHeight;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();};new ResizeObserver(resize).observe(container);resize();
 let previous=performance.now();function frame(now){requestAnimationFrame(frame);const dt=Math.min((now-previous)/1000,.1);previous=now;consoleWorld.frame(now,dt);orbit.update();renderer.render(scene,camera);}requestAnimationFrame(frame);
 return {update,setActivity:(phase,text)=>consoleWorld.setActivity(phase,text),operate:(message,cancelled)=>consoleWorld.operate(message,cancelled),focusFly(){camera.position.set(2600,2850,3500);orbit.target.copy(consoleWorld.position);orbit.update();},resetCamera(){camera.position.set(4700,3200,6200);orbit.target.set(0,450,0);orbit.update();},toggleSurface(){visible=!visible;headGroup.visible=visible;return visible;},toggleSection(){section=!section;camera.position.set(...(section?[0,600,8200]:[4700,3200,6200]));orbit.target.set(0,450,0);orbit.update();return section;}};
}
