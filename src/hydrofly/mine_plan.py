"""Piecewise annual pumping, evaluated by timflow with full prior-year memory."""
from functools import lru_cache
from typing import Literal
import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator
from scipy.optimize import linprog
from hydrofly.engine import Aquifer, SUPERPIT, build_model, heads

class MinePlan(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    bore_count:int=Field(default=10,ge=4,le=16)
    floors:list[float]=Field(default_factory=lambda:[-375-8*i for i in range(10)],min_length=1,max_length=10)
    rates:list[list[float]]=Field(default_factory=lambda:[[500.]*10 for _ in range(10)])
    objective:Literal['cost','rate','drawdown']='rate'
    conductivity:float=Field(default=.1,ge=.0001,le=5)
    thickness:float=Field(default=200,ge=100,le=400)
    storativity:float=Field(default=.001,ge=.0001,le=.01)
    capacity:float=Field(default=6000,ge=100,le=10000)
    view_extent:float=Field(default=10000,ge=2600,le=20000)
    initial_floor:float=Field(default=-350,ge=-600,le=360)
    active_year:int=Field(default=0,ge=0,le=9)

    @model_validator(mode='after')
    def valid(self):
        if len(self.rates)!=len(self.floors) or any(len(q)!=self.bore_count for q in self.rates):raise ValueError('One rate per bore per year is required')
        if any(not np.isfinite(h) or not -600<=h<=-366 for h in self.floors):raise ValueError('Floor elevations must be −600 to −366 m AHD')
        if self.floors[0]>self.initial_floor:raise ValueError('First floor must be below the initial floor')
        if any(b>a for a,b in zip(self.floors,self.floors[1:])):raise ValueError('Pit floors must stay level or deepen each year')
        if any(not np.isfinite(q) or not 0<=q<=self.capacity for row in self.rates for q in row):raise ValueError('Rates must be within bore capacity')
        if self.active_year>=len(self.floors):raise ValueError('Selected year is outside the plan')
        return self

    def aquifer(self):return Aquifer(self.conductivity,self.thickness,self.storativity,-365,-900)
    def wells(self):
        a=np.arange(self.bore_count)*2*np.pi/self.bore_count
        return np.column_stack((2140*np.cos(a),1055*np.sin(a)))
    def key(self):return (self.bore_count,len(self.floors),self.aquifer())

def view_grid(extent=10000):
    # Keep the original central sampling and add outer points for regional context.
    outer=np.linspace(2600,extent,6)[1:] if extent>2600 else np.array([])
    axis=np.unique(np.r_[-outer[::-1],np.linspace(-2600,2600,25),outer])
    x,y=np.meshgrid(axis,axis)
    return axis,np.column_stack((x.ravel(),y.ravel()))

AXIS,GRID=view_grid()

@lru_cache(maxsize=3)
def kernels(count,years,aq,grid=False,extent=10000):
    angle=np.arange(count)*2*np.pi/count
    wells=np.column_stack((2140*np.cos(angle),1055*np.sin(angle)))
    points=np.vstack((SUPERPIT.controls,wells,view_grid(extent)[1])) if grid else np.vstack((SUPERPIT.controls,wells))
    times=np.arange(1,years*12+1)*365/12
    result=[]
    for well in wells:
        m=build_model(aq,[well],[[(0,1000)]],tmax=365*years)
        result.append((aq.initial_head-heads(m,points,times,aq))/1000)
    # [month lag, point, bore]. G(0)=0; all evaluations are >=365/12 days after steps.
    a=np.transpose(np.array(result),(2,1,0));a.setflags(write=False)
    return a

def design_matrix(plan,grid=False):
    g=kernels(*plan.key(),grid,plan.view_extent if grid else 10000)
    months,points,count=g.shape;years=len(plan.floors)
    a=np.zeros((months,points,years,count))
    for t in range(months):
        for year in range(years):
            lag=t-12*year
            if lag>=0:a[t,:,year,:]=g[lag]-(g[lag-12] if lag>=12 else 0)
    return a.reshape(months,points,years*count)

def numerical(plan,grid=False):
    a=design_matrix(plan,grid)
    return plan.aquifer().initial_head-a@np.array(plan.rates).ravel()

def floor_at(plan,day):
    # Right-continuous steps: the new bench applies exactly at its year-end date.
    index=min(max(int(day//365),0),len(plan.floors))
    return float([plan.initial_floor,*plan.floors][index])

def target_heads(plan):
    indices=np.arange(1,len(plan.floors)*12+1)//12
    return np.asarray([plan.initial_floor,*plan.floors])[indices]-5

def timeline(plan,h):
    times=np.arange(len(plan.floors)*12+1)*365/12
    highest=np.r_[plan.aquifer().initial_head,h[:,:25].max(axis=1)]
    return [{'day':float(day),'head':float(head),'floor':floor_at(plan,day),'target':floor_at(plan,day)-5} for day,head in zip(times,highest)]

def unit_costs(plan):
    # Deliberately synthetic operating costs, AUD/m3; no site tariff claim.
    return .04+.06*np.arange(plan.bore_count)/max(plan.bore_count-1,1)

def objective_metric(plan,q,h):
    q=np.asarray(q).reshape(-1,plan.bore_count)
    if plan.objective=='rate':return float(q.sum()/(q.size*plan.capacity))
    if plan.objective=='cost':return float((q*unit_costs(plan)).sum()/(len(plan.floors)*plan.capacity*unit_costs(plan).sum()))
    targets=target_heads(plan)[:,None]
    return float(np.mean(np.maximum(targets-h[:,:25],0)/np.maximum(-365-targets,1)))

def cost(plan,h=None):
    h=numerical(plan) if h is None else h
    targets=target_heads(plan)
    scale=np.maximum(-365-targets,1)
    deficit=np.maximum(h[:,:25]-targets[:,None],0)/scale[:,None]
    return float(objective_metric(plan,plan.rates,h)+10000*np.mean(deficit**2))

def evaluate_plan(plan,grid=True):
    h=numerical(plan,grid);years=len(plan.floors);summaries=[]
    for year in range(years):
        target=plan.floors[year]-5;quarter=h[12*year:12*year+12,:25];q=np.array(plan.rates[year])
        summaries.append({'year':year+1,'floor':plan.floors[year],'target':target,'worst_head':float(quarter.max()),
          'end_head':float(quarter[-1].max()),'quarter_heads':quarter[[2,5,8,11]].max(axis=1).tolist(),
          'feasible':bool(np.all(quarter<=target_heads(plan)[12*year:12*year+12,None]+1e-5)),'total_rate':float(q.sum()),'volume':float(q.sum()*365),
          'active_bores':int(np.count_nonzero(q>1e-6))})
    index=12*years-1
    result={'years':summaries,'rates':plan.rates,'score':cost(plan,h),'total_volume':sum(y['volume'] for y in summaries),
      'feasible':bool(plan.aquifer().initial_head<=plan.initial_floor-5 and all(y['feasible'] for y in summaries)),'confined_valid':bool(h[:,:25+plan.bore_count].min()>-900),
      'wells':plan.wells().tolist(),'axis':view_grid(plan.view_extent)[0].tolist(),'view_extent':plan.view_extent,'active_year':years-1,
      'target':plan.floors[-1]-5,'floor':plan.floors[-1],
      'objective':plan.objective,'objective_metric':objective_metric(plan,plan.rates,h),
      'operating_cost_aud':float((np.asarray(plan.rates)*unit_costs(plan)).sum()*365),'unit_costs':unit_costs(plan).tolist(),
      'conductivity':plan.conductivity,'transmissivity':plan.conductivity*plan.thickness,
      'engine':'timflow.transient 0.5.0','assessment':'Monthly controls across the complete plan; initial condition checked',
      'timeline':timeline(plan,h),'initial_floor':plan.initial_floor,'duration_days':365*years}
    if grid:result['surface']=h[index,25+plan.bore_count:].reshape(len(view_grid(plan.view_extent)[0]),-1).tolist()
    return result

def benchmark(plan):
    if plan.aquifer().initial_head>plan.initial_floor-5:return {'success':False,'message':'The day-zero target is already missed before pumping starts. Raise the initial floor or provide a separate pre-dewatering model.'}
    a=design_matrix(plan);n=plan.bore_count*len(plan.floors)
    controls=a[:,:25,:].reshape(-1,n)
    target=target_heads(plan)
    required=np.repeat(-365-target+1e-5,25)
    # Confined validity at all modelled pit/well monthly samples.
    limits=a.reshape(-1,n)
    coefficients=np.ones(n)
    if plan.objective=='cost':coefficients=np.tile(unit_costs(plan),len(plan.floors))
    elif plan.objective=='drawdown':
        # With head <= target enforced, excess drawdown is a linear objective.
        scale=np.maximum(-365-target,1)
        coefficients=(a[:,:25,:]/scale[:,None,None]).sum(axis=(0,1))
    result=linprog(coefficients,A_ub=np.vstack((-controls,limits)),
       b_ub=np.r_[-required,np.full(len(limits),535-1e-5)],bounds=[(0,plan.capacity)]*n,method='highs')
    if not result.success:return {'success':False,'message':'No feasible monthly plan within these capacities and confined assumptions.'}
    updated=plan.model_copy(update={'rates':result.x.reshape(-1,plan.bore_count).tolist()})
    return {'success':True,'result':evaluate_plan(updated),'message':f'Minimum {plan.objective} benchmark under monthly targets; active-bore count is not explicitly minimised.'}


class SimulationRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    plan:MinePlan
    start:int=Field(default=0,ge=0,le=120)
    count:int=Field(default=4,ge=1,le=6)

def simulation_frames(request):
    """Incremental frames from one uninterrupted pumping history, no annual resets."""
    p=request.plan;n=len(p.floors)*12
    if request.start>n:raise ValueError('Frame outside the plan')
    frames=[];g=None;axis,grid_points=view_grid(p.view_extent)
    for step in range(request.start,min(n+1,request.start+request.count)):
        day=step*365/12;year=min(step//12,len(p.floors)-1)
        # The exact step has zero instantaneous response; previous pulses persist.
        values=np.full(25+p.bore_count+len(grid_points),p.aquifer().initial_head,dtype=float)
        if step:
            if g is None:g=kernels(*p.key(),True,p.view_extent)
            for k,q in enumerate(p.rates):
                lag=step-12*k
                if lag>0:values-=(g[lag-1]-(g[lag-13] if lag>12 else 0))@np.array(q)
        floor=floor_at(p,day);head=float(values[:25].max())
        volume=sum(sum(q)*min(max(day-k*365,0),365) for k,q in enumerate(p.rates))
        frames.append({'day':day,'head':head,'floor':floor,'target':floor-5,'active_year':year,
            'feasible':bool(head<=floor-5+1e-5),'confined_valid':bool(values[:25+p.bore_count].min()>p.aquifer().roof),
            'surface':values[25+p.bore_count:].reshape(len(axis),len(axis)).tolist(),'volume_to_date':volume})
    return {'frames':frames,'next':request.start+len(frames),'done':request.start+len(frames)>n,
        'wells':p.wells().tolist(),'axis':axis.tolist(),'view_extent':p.view_extent,'rates':p.rates,'duration_days':n*365/12,
        'initial_floor':p.initial_floor,'years':[{'year':i+1,'floor':h,'target':h-5} for i,h in enumerate(p.floors)]}
