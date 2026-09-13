"""One-well-at-a-time policy. Decisions do not apply pumping actions."""
from typing import Literal
import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator
from hydrofly.engine import CLASSIC, Aquifer, response, validate_rates, QMAX
from hydrofly.agents import objective

class Strategy(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    search: Literal['greedy','patrol','protect_worst']='greedy'
    step: float=Field(default=500,ge=1,le=6000)
    minimum_step: float=Field(default=25,ge=1,le=6000)
    trim_when_safe: bool=True
    well_order: list[int]=Field(default_factory=lambda:list(range(1,11)))
    max_moves: int=Field(default=200,ge=1,le=1000)

    @model_validator(mode='after')
    def valid(self):
        if sorted(self.well_order)!=list(range(1,11)): raise ValueError('well_order must contain wells 1–10 once each')
        if self.minimum_step>self.step: raise ValueError('minimum_step must not exceed step')
        return self

class FlyState(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    moves: int=Field(default=0,ge=0,le=1000)
    cursor: int=Field(default=0,ge=0,le=9)
    step: float | None=Field(default=None,ge=1,le=6000)

def decide(rates,aquifer=Aquifer(),day=30,level=CLASSIC,strategy=None,state=None):
    strategy=strategy or Strategy();state=state or FlyState()
    q=validate_rates(rates)
    if state.moves>=strategy.max_moves:
        return {'done':True,'reason':'Move budget reached. No claim of optimality.'}
    # The response basis is evaluated by timflow, including well heads for validity.
    a=response(aquifer,day,True,level)[:35]
    h=aquifer.initial_head-a@q
    if h.min()<=aquifer.roof:
        return {'done':True,'reason':'Current design violates the confined assumption. Reset pumping or aquifer settings.'}
    safe=h[:25].max()<=level.target+1e-5
    if safe and not strategy.trim_when_safe:
        return {'done':True,'reason':'Target reached. Trimming is disabled in your strategy.'}
    step=min(state.step or strategy.step,strategy.step)
    current_deficit=float(np.sum(np.maximum(h[:25]-level.target,0)**2))
    order=strategy.well_order[state.cursor:]+strategy.well_order[:state.cursor]
    while True:
        candidates=[]
        for number in order:
            i=number-1;trial=q.copy();trial[i]=np.clip(q[i]+(-step if safe else step),0,QMAX)
            if trial[i]==q[i]: continue
            heads=aquifer.initial_head-a@trial
            if heads.min()<=aquifer.roof: continue
            feasible=heads[:25].max()<=level.target+1e-5
            deficit=float(np.sum(np.maximum(heads[:25]-level.target,0)**2))
            if safe and not feasible: continue
            if not safe and deficit>=current_deficit-1e-12: continue
            cost=objective(trial,heads[:25],aquifer,level)['score']
            candidates.append((i,trial[i],float(heads[:25].max()),deficit,cost))
        if candidates:
            if strategy.search=='patrol': chosen=candidates[0]
            elif strategy.search=='protect_worst' and not safe: chosen=min(candidates,key=lambda c:(c[2],c[4]))
            else: chosen=min(candidates,key=lambda c:(c[3],c[4]) if not safe else (c[4],))
            i,value,worst,_,cost=chosen
            return {'done':False,'well':i,'from_rate':float(q[i]),'to_rate':float(value),
                    'predicted_worst_head':worst,'predicted_score':cost,
                    'reason':f"{strategy.search}: {'trim surplus pumping' if safe else 'reduce pit head deficit'}",
                    'state':{'moves':state.moves+1,'cursor':(strategy.well_order.index(i+1)+1)%10,'step':step}}
        if step<=strategy.minimum_step:
            return {'done':True,'reason':'No admissible single-well move at the minimum step. Local stopping point, not a global optimum.'}
        step=max(strategy.minimum_step,step/2)
