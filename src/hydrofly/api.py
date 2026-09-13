"""Same-origin API and frontend. Requests contain a complete scenario."""
from contextlib import asynccontextmanager
from pathlib import Path
import os
import threading
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ConfigDict
from hydrofly.engine import Aquifer, WELLS, CONTROL_POINTS, evaluate, response, LEVELS
from hydrofly.agents import objective, ConventionalPolicy
from hydrofly.fly import Strategy, FlyState, decide

work_lock=threading.Lock()


@asynccontextmanager
async def lifespan(app):
    if os.getenv("HYDROFLY_SKIP_WARMUP") != "1": response()
    yield


app=FastAPI(title="HydroFly",version="0.2.0",lifespan=lifespan)


class Scenario(BaseModel):
    model_config=ConfigDict(extra="forbid",allow_inf_nan=False)
    rates:list[float]=Field(default_factory=lambda:[2000.]*10,min_length=10,max_length=10)
    level:Literal["classic","superpit"]="classic"
    day:float=Field(default=30,ge=.1,le=365)
    conductivity:float=Field(default=10,ge=.01,le=25)
    thickness:float=Field(default=80,ge=40,le=500)
    storativity:float=Field(default=.001,ge=.0001,le=.02)

    def aquifer(self):
        base=LEVELS[self.level].aquifer
        return Aquifer(self.conductivity,self.thickness,self.storativity,base.initial_head,base.roof)


def run_job(fn):
    # Bound expensive public work. No unbounded model queue or cache.
    if not work_lock.acquire(blocking=False):raise HTTPException(429,"Model is busy. Try again shortly.")
    try:return fn()
    except ValueError as exc:raise HTTPException(422,str(exc)) from exc
    finally:work_lock.release()


@app.get("/api/health")
def health():return {"status":"ok","engine":"timflow.transient 0.5.0"}


@app.get("/api/config")
def config(level:Literal["classic","superpit"]="superpit"):
    v=LEVELS[level]
    return {"level":v.name,"wells":v.wells.tolist(),"controls":v.controls.tolist(),
            "pit_floor":v.floor,"target":v.target,"initial_head":v.aquifer.initial_head,
            "well_capacity":6000,"aquifer_roof":v.aquifer.roof,"crest":v.crest,
            "floor_rx":v.floor_rx,"floor_ry":v.floor_ry,"rim_rx":v.rim_rx,"rim_ry":v.rim_ry,
            "extent":v.extent,"defaults":{"day":v.day,"conductivity":v.aquifer.conductivity,
            "thickness":v.aquifer.thickness,"storativity":v.aquifer.storativity}}


@app.post("/api/evaluate")
def calculate(s:Scenario):
    def compute():
        aq=s.aquifer();r=evaluate(s.rates,aq,s.day,level=LEVELS[s.level])
        return {**r,**objective(r['rates'],r['control_heads'],aq,LEVELS[s.level])}
    return run_job(compute)


@app.post("/api/optimise")
def optimise(s:Scenario):
    def compute():
        aq=s.aquifer();result=ConventionalPolicy().optimise(s.rates,aq,s.day,LEVELS[s.level])
        # Every replay frame is evaluated in Python. The browser never creates heads.
        result['frames']=[{**evaluate(step['rates'],aq,s.day,level=LEVELS[s.level]),**step} for step in result['trace']]
        return result
    return run_job(compute)


class FlyRequest(Scenario):
    strategy:Strategy=Field(default_factory=Strategy)
    state:FlyState=Field(default_factory=FlyState)

@app.post("/api/fly/decide")
def fly_decide(s:FlyRequest):
    return run_job(lambda:decide(s.rates,s.aquifer(),s.day,LEVELS[s.level],s.strategy,s.state))

@app.post("/api/fly/act")
def fly_act(s:FlyRequest):
    def compute():
        aq=s.aquifer();level=LEVELS[s.level]
        action=decide(s.rates,aq,s.day,level,s.strategy,s.state)
        if action['done']: return action
        q=list(s.rates);q[action['well']]=action['to_rate']
        result=evaluate(q,aq,s.day,level=level)
        return {**action,'result':{**result,**objective(q,result['control_heads'],aq,level),
                                  'iteration':action['state']['moves']}}
    return run_job(compute)


web=Path(os.getenv("HYDROFLY_WEB",Path(__file__).resolve().parents[2]/"dist"))
if web.exists():app.mount("/",StaticFiles(directory=web,html=True),name="web")
