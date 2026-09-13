// Illustrative highlights for software events, never a biological spike map.
export function createBrainActivity(windowElement){
 const image=windowElement.querySelector('img'),canvas=document.createElement('canvas');
 canvas.className='brain-activity';canvas.setAttribute('aria-hidden','true');windowElement.append(canvas);
 const ctx=canvas.getContext('2d');if(!ctx)return {flash(){}};
 const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
 let anchors=[],bursts=[],counter=0,frameId=0;
 function resize(){
  canvas.width=Math.max(1,windowElement.clientWidth);canvas.height=Math.max(1,windowElement.clientHeight);
  anchors=[];if(!image.complete||!image.naturalWidth)return;
  const source=document.createElement('canvas');source.width=canvas.width;source.height=canvas.height;
  const c=source.getContext('2d'),scale=Math.max(canvas.width/image.naturalWidth,canvas.height/image.naturalHeight);
  c.drawImage(image,(canvas.width-image.naturalWidth*scale)/2,(canvas.height-image.naturalHeight*scale)/2,image.naturalWidth*scale,image.naturalHeight*scale);
  const pixels=c.getImageData(0,0,canvas.width,canvas.height).data;
  for(let y=10;y<canvas.height-20;y+=5)for(let x=5;x<canvas.width-5;x+=5){const i=4*(y*canvas.width+x);if(pixels[i]+pixels[i+1]+pixels[i+2]>270)anchors.push([x,y]);}
 }
 new ResizeObserver(resize).observe(windowElement);image.addEventListener('load',resize);resize();
 function draw(now){
  ctx.clearRect(0,0,canvas.width,canvas.height);bursts=bursts.filter(b=>now-b.time<1200);
  for(const b of bursts){const age=(now-b.time)/1200,opacity=Math.sin(Math.PI*age)*.8;
   for(let i=0;i<b.count&&anchors.length;i++){const [x,y]=anchors[(b.seed*37+i*53)%anchors.length];ctx.globalAlpha=opacity;ctx.fillStyle=b.color;ctx.shadowColor=b.color;ctx.shadowBlur=9;ctx.beginPath();ctx.arc(x,y,1.2+Math.sin(age*Math.PI),0,Math.PI*2);ctx.fill();}
  }
  ctx.globalAlpha=1;ctx.shadowBlur=0;frameId=bursts.length?requestAnimationFrame(draw):0;
 }
 return {flash(kind='sense',strength=1){
  if(reduced||!anchors.length)return;
  bursts.push({time:performance.now(),seed:++counter,count:Math.min(45,Math.max(8,Math.round(15*strength))),color:kind==='update'?'#ceff71':kind==='action'?'#ffd88a':'#8ce6f0'});
  bursts=bursts.slice(-4);if(!frameId)frameId=requestAnimationFrame(draw);
 }};
}
