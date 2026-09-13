import test from 'node:test';
import assert from 'node:assert/strict';
import {playFly} from './game-loop.js';
test('fly must arrive before one actuator call, then use the new state',async()=>{
 const events=[];
 const r=await playFly({request:{rates:[0],state:{}},single:true,cancelled:()=>false,
 decide:async()=>{events.push('decide');return {done:false,well:0};},
 travel:async()=>{events.push('arrive');return true;},
 act:async()=>{events.push('act');return {result:{rates:[500]},state:{moves:1}};},
 show:()=>events.push('show')});
 assert.deepEqual(events,['decide','arrive','act','show']);assert.deepEqual(r.rates,[500]);assert.equal(r.state.moves,1);
});
test('pause during travel prevents pumping',async()=>{
 let paused=false;
 await playFly({request:{},cancelled:()=>paused,decide:async()=>({done:false}),
 travel:async()=>{paused=true;return false;},act:()=>assert.fail('pump changed before arrival'),show:()=>{}});
});
test('pause during actuator request still displays the applied result',async()=>{
 let paused=false,shown=false;
 const r=await playFly({request:{},cancelled:()=>paused,decide:async()=>({done:false}),travel:async()=>true,
 act:async()=>{paused=true;return {result:{rates:[500]},state:{moves:1}};},show:()=>{shown=true;}});
 assert.ok(shown);assert.equal(r.state.moves,1);
});
