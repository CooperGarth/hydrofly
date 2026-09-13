"""Client-carried JSON learning state for stateless Python function deployments.

No pickle, code execution, credentials or shared server sessions. Checkpoints
belong to the visitor's experiment and are validated on every request.
"""
import json
from typing import Literal
import numpy as np
from pydantic import BaseModel,ConfigDict,Field,model_validator
from hydrofly.learning import Agent,LearningStart

class Checkpoint(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    request:LearningStart
    q:dict[str,list[float]]=Field(default_factory=dict,max_length=500)
    episodes:int=Field(default=0,ge=0,le=100000)
    updates:int=Field(default=0,ge=0,le=8000000)
    cursor:int=Field(default=0,ge=0,le=160)
    history:list[dict]=Field(default_factory=list,max_length=100)
    rng:str=Field(max_length=1000)
    running:list[float]|None=None
    run_moves:int=Field(default=0,ge=0,le=80)
    visited:list[list[float]]=Field(default_factory=list,max_length=80)

    @model_validator(mode='after')
    def validate_arrays(self):
        n=self.request.plan.bore_count*len(self.request.plan.floors)
        if any(len(k)>128 or len(v)!=2*n+1 or not np.isfinite(v).all() or np.max(np.abs(v))>1e6 for k,v in self.q.items()):raise ValueError('Invalid Q-table')
        for row in self.visited+([] if self.running is None else [self.running]):
            if len(row)!=n or not np.isfinite(row).all() or min(row)<0 or max(row)>self.request.plan.capacity:raise ValueError('Invalid checkpoint rates')
        # History is display evidence only; limit encoded size and reject non-finite JSON.
        if len(json.dumps(self.history,allow_nan=False))>500000:raise ValueError('Checkpoint history too large')
        return self

class PortableRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    operation:Literal['start','episode','run','decide','act','export']
    request:LearningStart|None=None
    checkpoint:Checkpoint|None=None

def restore(checkpoint):
    a=Agent(checkpoint.request);a.max_states=500
    a.q={k:np.array(v,float) for k,v in checkpoint.q.items()}
    a.episodes=checkpoint.episodes;a.updates=checkpoint.updates;a.cursor=checkpoint.cursor
    a.history=checkpoint.history
    try:a.rng.bit_generator.state=json.loads(checkpoint.rng)
    except (ValueError,TypeError,KeyError,OverflowError) as exc:raise ValueError('Invalid random generator state') from exc
    a.running=None if checkpoint.running is None else np.array(checkpoint.running)
    a.run_moves=checkpoint.run_moves;a.visited={tuple(q) for q in checkpoint.visited}
    return a

def checkpoint(a):
    return {'request':a.request.model_dump(),'q':{k:v.tolist() for k,v in a.q.items()},
      'episodes':a.episodes,'updates':a.updates,'cursor':a.cursor,'history':a.history,
      'rng':json.dumps(a.rng.bit_generator.state),'running':None if a.running is None else a.running.tolist(),
      'run_moves':getattr(a,'run_moves',0),'visited':[list(q) for q in getattr(a,'visited',set())]}

def handle(p):
    if p.operation=='start':
        if p.request is None:raise ValueError('A mine plan and strategy are required')
        a=Agent(p.request);a.max_states=500
        value={'session':'portable','signature':a.signature,'algorithm':'Tabular Q-learning','alpha':.2,'gamma':.95}
    else:
        if p.checkpoint is None:raise ValueError('Learning checkpoint required')
        a=restore(p.checkpoint)
        if p.operation=='episode':value=a.episode()
        elif p.operation=='run':value=a.start_run()
        elif p.operation=='decide':value=a.decision()
        elif p.operation=='act':value=a.act()
        else:value={'algorithm':'Q-learning','signature':a.signature,'request':a.request.model_dump(),
            'history':a.history,'q_table':{k:v.tolist() for k,v in a.q.items()},'episodes':a.episodes,'updates':a.updates}
    return {'value':value,'checkpoint':checkpoint(a)}
