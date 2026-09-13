"""Piecewise annual pumping, evaluated by timflow with full prior-year memory."""
from functools import lru_cache
import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator
from scipy.optimize import linprog
from hydrofly.engine import Aquifer, SUPERPIT, build_model, heads

class MinePlan(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    bore_count:int=Field(default=10,ge=4,le=16)
    floors:list[float]=Field(default_factory=lambda:[-375,-382,-390],min_length=1,max_length=5)
    rates:list[list[float]]=Field(default_factory=lambda:[[500.]*10 for _ in range(3)])
    conductivity:float=Field(default=.2,ge=.05,le=5)
    thickness:float=Field(default=200,ge=100,le=400)
    storativity:float=Field(default=.001,ge=.0001,le=.01)
    capacity:float=Field(default=6000,ge=100,le=10000)
    active_year:int=Field(default=0,ge=0,le=4)

    @model_validator(mode='after')
    def valid(self):
        if len(self.rates)!=len(self.floors) or any(len(q)!=self.bore_count for q in self.rates):raise ValueError('One rate per bore per year is required')
        if any(not np.isfinite(h) or not -600<=h<=-366 for h in self.floors):raise ValueError('Floor elevations must be −600 to −366 m AHD')
        if any(b>a for a,b in zip(self.floors,self.floors[1:])):raise ValueError('Pit floors must stay level or deepen each year')
        if any(not np.isfinite(q) or not 0<=q<=self.capacity for row in self.rates for q in row):raise ValueError('Rates must be within bore capacity')
        if self.active_year>=len(self.floors):raise ValueError('Selected year is outside the plan')
        return self

    def aquifer(self):return Aquifer(self.conductivity,self.thickness,self.storativity,-365,-900)
    def wells(self):
        a=np.arange(self.bore_count)*2*np.pi/self.bore_count
        return np.column_stack((2140*np.cos(a),1055*np.sin(a)))
    def key(self):return (self.bore_count,len(self.floors),self.aquifer())

AXIS=np.linspace(-2600,2600,25)
_x,_y=np.meshgrid(AXIS,AXIS)
GRID=np.column_stack((_x.ravel(),_y.ravel()))

@lru_cache(maxsize=3)
def kernels(count,years,aq,grid=False):
    angle=np.arange(count)*2*np.pi/count
    wells=np.column_stack((2140*np.cos(angle),1055*np.sin(angle)))
    points=np.vstack((SUPERPIT.controls,wells,GRID)) if grid else np.vstack((SUPERPIT.controls,wells))
    times=np.arange(1,years*4+1)*365/4
    result=[]
    for well in wells:
        m=build_model(aq,[well],[[(0,1000)]],tmax=365*years)
        result.append((aq.initial_head-heads(m,points,times,aq))/1000)
    # [quarter lag, point, bore]. G(0)=0; all evaluations are >=91.25 days after steps.
    a=np.transpose(np.array(result),(2,1,0));a.setflags(write=False)
    return a

def design_matrix(plan,grid=False):
    g=kernels(*plan.key(),grid)
    quarters,points,count=g.shape;years=len(plan.floors)
    a=np.zeros((quarters,points,years,count))
    for t in range(quarters):
        for year in range(years):
            lag=t-4*year
            if lag>=0:a[t,:,year,:]=g[lag]-(g[lag-4] if lag>=4 else 0)
    return a.reshape(quarters,points,years*count)

def numerical(plan,grid=False):
    a=design_matrix(plan,grid)
    return plan.aquifer().initial_head-a@np.array(plan.rates).ravel()

def cost(plan,h=None):
    h=numerical(plan) if h is None else h
    targets=np.repeat(np.array(plan.floors)-5,4)
    scale=np.maximum(-365-targets,1)
    deficit=np.maximum(h[:,:25]-targets[:,None],0)/scale[:,None]
    q=np.asarray(plan.rates)
    return float(q.sum()/(q.size*plan.capacity)+10000*np.mean(deficit**2)+.03*np.count_nonzero(q)/q.size)

def evaluate_plan(plan,grid=True):
    h=numerical(plan,grid);years=len(plan.floors);summaries=[]
    for year in range(years):
        target=plan.floors[year]-5;quarter=h[4*year:4*year+4,:25];q=np.array(plan.rates[year])
        summaries.append({'year':year+1,'floor':plan.floors[year],'target':target,'worst_head':float(quarter.max()),
          'end_head':float(quarter[-1].max()),'quarter_heads':quarter.max(axis=1).tolist(),
          'feasible':bool(quarter.max()<=target+1e-5),'total_rate':float(q.sum()),'volume':float(q.sum()*365),
          'active_bores':int(np.count_nonzero(q>1e-6))})
    index=4*plan.active_year+3
    result={'years':summaries,'rates':plan.rates,'score':cost(plan,h),'total_volume':sum(y['volume'] for y in summaries),
      'feasible':all(y['feasible'] for y in summaries),'confined_valid':bool(h[:,:25+plan.bore_count].min()>-900),
      'wells':plan.wells().tolist(),'axis':AXIS.tolist(),'active_year':plan.active_year,
      'target':plan.floors[plan.active_year]-5,'floor':plan.floors[plan.active_year],
      'engine':'timflow.transient 0.5.0','assessment':'Quarterly controls; displayed mesh is year end'}
    if grid:result['surface']=h[index,25+plan.bore_count:].reshape(25,25).tolist()
    return result

def benchmark(plan):
    a=design_matrix(plan);n=plan.bore_count*len(plan.floors)
    controls=a[:,:25,:].reshape(-1,n)
    target=np.repeat(np.array(plan.floors)-5,4)
    required=np.repeat(-365-target+1e-5,25)
    # Confined validity at all modelled pit/well quarterly samples.
    limits=a.reshape(-1,n)
    result=linprog(np.ones(n),A_ub=np.vstack((-controls,limits)),
       b_ub=np.r_[-required,np.full(len(limits),535-1e-5)],bounds=[(0,plan.capacity)]*n,method='highs')
    if not result.success:return {'success':False,'message':'No feasible quarterly plan within these capacities and confined assumptions.'}
    updated=plan.model_copy(update={'rates':result.x.reshape(-1,plan.bore_count).tolist()})
    return {'success':True,'result':evaluate_plan(updated),'message':'Minimum total volume benchmark; bore-count sparsity is not guaranteed.'}
