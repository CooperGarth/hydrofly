"""Model-assisted linear action-value learning over complete pumping schedules.

Shared action features transfer experience between schedules. This remains an
experimental learner, not a convergence guarantee or biological neural model.
"""
from collections import OrderedDict
import hashlib,json,secrets
import numpy as np
from pydantic import BaseModel, ConfigDict, Field
from hydrofly.mine_plan import MinePlan, design_matrix, evaluate_plan, objective_metric, target_heads

class LearningStart(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    plan:MinePlan
    strategy:str=Field(default='greedy',pattern='^(greedy|patrol|sparse)$')
    step:float=Field(default=250,ge=25,le=2000)
    guidance:float=Field(default=.65,ge=0,le=1)
    max_moves:int=Field(default=200,ge=20,le=400)
    seed:int=Field(default=42,ge=0,le=2147483647)

class LearnRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    session:str=Field(min_length=16,max_length=64)

class Agent:
    def __init__(self,request):
        self.request=request;self.plan=request.plan;self.a=design_matrix(self.plan)
        self.q={};self.episodes=0;self.updates=0;self.history=[]
        self.rng=np.random.default_rng(request.seed);self.cursor=0
        self.n=self.plan.bore_count*len(self.plan.floors);self.actions=2*self.n+1
        self.targets=target_heads(self.plan)[:,None]
        self.scale=np.maximum(self.plan.initial_head-self.targets,1)
        self.running=None;self.pending=None
        self.weights=np.zeros(7);self.best=np.array(self.plan.rates,dtype=float).ravel()
        self._feature_cache={};self._observations={}
        self.signature=hashlib.sha256(json.dumps(request.model_dump(),sort_keys=True).encode()).hexdigest()

    def validate_start(self):
        if self.plan.initial_head>self.plan.initial_floor-5:
            raise ValueError('Day 0 already misses the target. Pumping starting on day 0 cannot instantly lower the initial head; revise the starting floor or initial head.')
        if self.observe(np.array(self.plan.rates).ravel())[0].min()<=self.plan.aquifer().roof:
            raise ValueError('Starting pumping rates lower sampled head below the confined aquifer roof. Reduce starting rates before training.')

    def observe(self,q):
        key=self.state(q)
        if key in self._observations:return self._observations[key]
        h=self.plan.initial_head-self.a@q
        deficits=np.maximum(h[:,:25]-self.targets,0)/self.scale
        pumping=float(q.sum()/(self.n*self.plan.capacity))
        active=float(np.count_nonzero(q)/self.n)
        safe=bool(self.plan.aquifer().initial_head<=self.plan.initial_floor-5 and deficits.max()<1e-7 and np.max(h[:,:25]-self.targets)<=1e-5 and h.min()>self.plan.aquifer().roof)
        loss=float(10000*np.mean(deficits**2)+objective_metric(self.plan,q,h))
        result=(h,deficits,pumping,active,safe,loss)
        if len(self._observations)>=8:self._observations.pop(next(iter(self._observations)))
        self._observations[key]=result
        return result

    def state(self,q):
        # Exact complete schedule, including all pumping history; no coarse bins.
        return hashlib.sha256(np.asarray(q,dtype='<f8').tobytes()).hexdigest()[:24]

    def improvement(self,old,new):
        # Match the feasibility-first ordering used by the incumbent and teacher.
        before=old[5] if old[4] else 10000*float(np.mean(old[1]**2))
        after=new[5] if old[4] else 10000*float(np.mean(new[1]**2))
        return float(np.tanh(10*(before-after)/max(before,1)))

    def features(self,q):
        key=self.state(q)
        if key in self._feature_cache:return self._feature_cache[key]
        old=self.observe(q);rows=[]
        for action in range(self.actions):
            new=self.observe(self.trial(q,action))
            improvement=self.improvement(old,new)
            rows.append([1.,improvement,float(new[4]),float(action==2*self.n),
                         float(action==2*self.n and new[4]),
                         float(new[0].min()<=self.plan.aquifer().roof),
                         float(action<self.n)-float(self.n<=action<2*self.n)])
        result=np.asarray(rows)
        # This is only a disposable model-evaluation cache, never learning memory.
        if len(self._feature_cache)>=4:self._feature_cache.pop(next(iter(self._feature_cache)))
        self._feature_cache[key]=result
        return result

    def values(self,q):
        key=self.state(q);values=self.features(q)@self.weights
        self.q={key:values}  # Last action values for existing diagnostic/export clients.
        return key,values

    def rank(self,q):
        h,d,p,a,safe,loss=self.observe(q)
        valid=h.min()>self.plan.aquifer().roof
        return (not valid,not safe,float(np.sum(d*d)) if not safe else loss)

    def retain(self,q):
        if self.rank(q)<self.rank(self.best):self.best=q.copy()

    def admissible(self,q):
        valid=np.r_[q<self.plan.capacity-1e-6,q>1e-6,True]
        # Stop is legal while unsafe but explicitly penalised.
        return np.flatnonzero(valid)

    def trial(self,q,action):
        result=q.copy()
        if action<2*self.n:
            i=action%self.n
            delta=np.clip((self.request.step if action<self.n else -self.request.step),-q[i],self.plan.capacity-q[i])
            old=self.observe(q)
            # Backtrack near a binding target or aquifer roof, down to <1 m³/day.
            for _ in range(13):
                result[i]=q[i]+delta;head=old[0]-self.a[:,:,i]*delta
                safe=np.max((head[:,:25]-self.targets)/self.scale)<1e-7 and np.max(head[:,:25]-self.targets)<=1e-5
                if head.min()>self.plan.aquifer().roof and (not old[4] or safe):break
                delta*=.5
            else:result[i]=q[i]
        return result

    def teacher(self,q):
        observation=self.observe(q);safe=observation[4];candidates=[]
        for action in self.admissible(q):
            if action==2*self.n:continue
            trial=self.trial(q,action);h,d,p,a,ok,loss=self.observe(trial)
            if h.min()<=self.plan.aquifer().roof or (safe and not ok):continue
            if self.rank(trial)>=self.rank(q):continue
            metric=float(np.sum(d*d)) if not safe else loss
            if safe and self.request.strategy=='sparse':metric+=.02*a
            candidates.append((int(action),metric))
        if not candidates:return 2*self.n
        if self.request.strategy=='patrol':
            candidates.sort(key=lambda c:(c[0]-self.cursor)%(2*self.n));self.cursor=(candidates[0][0]+1)%(2*self.n)
            return candidates[0][0]
        return min(candidates,key=lambda c:c[1])[0]

    def transition(self,q,action):
        old=self.observe(q);trial=self.trial(q,action);new=self.observe(trial)
        if action==2*self.n:return trial,(0. if new[4] else -3),True
        if new[0].min()<=self.plan.aquifer().roof:return q.copy(),-2.,False
        return trial,float(self.improvement(old,new)-.001),False

    def update(self,key,action,reward,next_q,terminal):
        matrix=self._feature_cache[key];features=matrix[action].copy()
        _,next_values=self.values(next_q)
        future=0 if terminal else float(next_values[self.admissible(next_q)].max())
        td=float(reward+.95*future-features@self.weights)
        self.weights+=.05*np.clip(td,-5,5)*features/(1+features@features)
        self.updates+=1
        self.q={key:matrix@self.weights}
        return td

    def episode(self):
        q=(np.array(self.plan.rates).ravel() if self.episodes%4==0 else self.best.copy());total=0.;tds=[];guide_count=0;explore_count=0
        epsilon=max(.05,.6*.965**self.episodes)
        guidance=self.request.guidance*max(.2,.995**self.episodes)
        for move in range(self.request.max_moves):
            key,values=self.values(q)
            if self.rng.random()<guidance:action=self.teacher(q);guide_count+=1
            elif self.rng.random()<epsilon:action=int(self.rng.choice(self.admissible(q)));explore_count+=1
            else:
                valid=self.admissible(q);best=values[valid].max();action=int(self.rng.choice(valid[np.isclose(values[valid],best)]))
            new,reward,terminal=self.transition(q,action)
            if move==self.request.max_moves-1 and not terminal:reward+=-3 if not self.observe(new)[4] else 0;terminal=True
            tds.append(abs(self.update(key,action,reward,new,terminal)));total+=reward;q=new;self.retain(q)
            if terminal:break
        self.episodes+=1
        record={'episode':self.episodes,'reward':total,'epsilon':epsilon,'guidance':guidance,
          'success':self.observe(q)[4],'experiment_score':self.observe(q)[5],'volume':float(q.sum()*365),'active_bore_years':int(np.count_nonzero(q)),
          'moves':move+1,'td_error':float(np.mean(tds)),'updates':self.updates,'states':self.updates,'parameters':len(self.weights),'best_score':self.observe(self.best)[5],'best_success':self.observe(self.best)[4],'best_volume':float(self.best.sum()*365),
          'guided_actions':guide_count,'exploratory_actions':explore_count,
          'last_action':int(action),'last_reward':float(reward),'last_state':key,
          'last_action_values':self.q.get(key,np.zeros(self.actions)).tolist()}
        self.history.append({k:v for k,v in record.items() if k!='last_action_values'});self.history=self.history[-100:]
        return {'metrics':record,'rates':self.best.reshape(-1,self.plan.bore_count).tolist(),'experiment_rates':q.reshape(-1,self.plan.bore_count).tolist(),'history':self.history}

    def start_run(self):
        self.running=np.array(self.plan.rates).ravel();self.pending=None;self.run_moves=0;self.visited=set()
        return evaluate_plan(self.plan)

    def decision(self):
        if self.running is None:raise ValueError('Start the learned-policy run first')
        if self.pending is not None:return self.pending
        key,values=self.values(self.running);valid=self.admissible(self.running)
        # A transparent model-based safeguard admits only improving complete plans.
        # Q-values rank those candidates; this is not a model-free policy test.
        improving=[int(a) for a in valid if a!=2*self.n and self.rank(self.trial(self.running,a))<self.rank(self.running)]
        ranked=sorted(improving,key=lambda a:values[a],reverse=True) if improving else [2*self.n]
        # Evaluation never calls the teacher and never explores randomly.
        action=int(ranked[0]);q=self.trial(self.running,action)
        terminal=action==2*self.n or self.run_moves>=self.request.max_moves or tuple(q) in self.visited
        self.pending={'done':bool(terminal),'action':action,'well':int(action%self.n%self.plan.bore_count),
          'year':int((action%self.n)//self.plan.bore_count),'from_rate':float(self.running[action%self.n]),
          'to_rate':float(q[action%self.n]),'state':key,'q_values':values.tolist(),
          'reason':'Learned Q-policy ranks hydraulically screened improving actions' if not terminal else 'No improving single-rate move, repeated design, or move budget reached. Feasibility is reported separately.',
          'learning':False,'episodes':self.episodes}
        return self.pending

    def act(self):
        decision=self.decision()
        if decision['done']:return decision
        q,reward,_=self.transition(self.running,decision['action']);self.running=q;self.retain(q);self.visited.add(tuple(q));self.run_moves+=1
        plan=self.plan.model_copy(update={'rates':self.best.reshape(-1,self.plan.bore_count).tolist(),'experiment_rates':q.reshape(-1,self.plan.bore_count).tolist(),'active_year':decision['year']})
        self.pending=None
        return {**decision,'reward':reward,'move':self.run_moves,'result':evaluate_plan(plan)}

SESSIONS=OrderedDict()
def new_session(request):
    agent=Agent(request);agent.validate_start();token=secrets.token_urlsafe(18);SESSIONS[token]=agent
    while len(SESSIONS)>8:SESSIONS.popitem(last=False)
    return {'session':token,'signature':agent.signature,'algorithm':'Model-assisted linear Q-learning','alpha':.05,'gamma':.95}
def get_agent(token):
    if token not in SESSIONS:raise ValueError('Learning session expired or server restarted. Start training again.')
    SESSIONS.move_to_end(token);return SESSIONS[token]
