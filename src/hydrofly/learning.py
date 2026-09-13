"""Strategy-guided tabular Q-learning, with inspectable Bellman updates.

State aggregation is intentionally small and partially observable. No neural or
connectome claims. Training and evaluation use the same synthetic mine plan.
"""
from collections import OrderedDict
import hashlib,json,secrets
import numpy as np
from pydantic import BaseModel, ConfigDict, Field
from hydrofly.mine_plan import MinePlan, design_matrix, evaluate_plan

class LearningStart(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    plan:MinePlan
    strategy:str=Field(default='greedy',pattern='^(greedy|patrol|sparse)$')
    step:float=Field(default=250,ge=25,le=2000)
    guidance:float=Field(default=.65,ge=0,le=1)
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
        self.targets=np.repeat(np.array(self.plan.floors)-5,4)[:,None]
        self.scale=np.maximum(-365-self.targets,1)
        self.running=None;self.pending=None
        self.signature=hashlib.sha256(json.dumps(request.model_dump(),sort_keys=True).encode()).hexdigest()

    def observe(self,q):
        h=-365-self.a@q
        deficits=np.maximum(h[:,:25]-self.targets,0)/self.scale
        pumping=float(q.sum()/(self.n*self.plan.capacity))
        active=float(np.count_nonzero(q)/self.n)
        safe=bool(deficits.max()<1e-7 and h.min()>self.plan.aquifer().roof)
        loss=float(np.mean(deficits**2)+.05*pumping+.015*active)
        return h,deficits,pumping,active,safe,loss

    def state(self,q):
        h,d,p,a,safe,loss=self.observe(q)
        worst=np.unravel_index(np.argmax(d),d.shape)
        # Explicit state aggregation: similar hydraulic states share Q values.
        return f'{worst[0]//4}:{worst[1]}:{min(int(d.max()*20),40)}:{min(int(p*40),40)}:{int(a*10)}:{int(safe)}'

    def values(self,q):
        key=self.state(q)
        if key not in self.q and len(self.q)<2000:self.q[key]=np.zeros(self.actions)
        return key,self.q.get(key,np.zeros(self.actions))

    def admissible(self,q):
        valid=np.r_[q<self.plan.capacity-1e-6,q>1e-6,True]
        # Stop is legal while unsafe but explicitly penalised.
        return np.flatnonzero(valid)

    def trial(self,q,action):
        result=q.copy()
        if action<2*self.n:
            i=action%self.n;result[i]=np.clip(result[i]+(self.request.step if action<self.n else -self.request.step),0,self.plan.capacity)
        return result

    def teacher(self,q):
        observation=self.observe(q);safe=observation[4];candidates=[]
        for action in self.admissible(q):
            if action==2*self.n:continue
            trial=self.trial(q,action);h,d,p,a,ok,loss=self.observe(trial)
            if h.min()<=-900 or (safe and not ok):continue
            if loss>=observation[5]-1e-10:continue
            metric=loss if self.request.strategy!='sparse' else loss+.02*a
            candidates.append((int(action),metric))
        if not candidates:return 2*self.n
        if self.request.strategy=='patrol':
            candidates.sort(key=lambda c:(c[0]-self.cursor)%(2*self.n));self.cursor=(candidates[0][0]+1)%(2*self.n)
            return candidates[0][0]
        return min(candidates,key=lambda c:c[1])[0]

    def transition(self,q,action):
        old=self.observe(q);trial=self.trial(q,action);new=self.observe(trial)
        if action==2*self.n:return trial,(5-new[2]-.3*new[3] if new[4] else -3),True
        if new[0].min()<=-900:return q.copy(),-2.,False
        return trial,float(20*(old[5]-new[5])-.01),False

    def update(self,key,action,reward,next_q,terminal):
        _,next_values=self.values(next_q)
        future=0 if terminal else float(next_values[self.admissible(next_q)].max())
        old=self.q.get(key,np.zeros(self.actions))[action]
        td=reward+.95*future-old
        if key in self.q:self.q[key][action]+= .2*td
        self.updates+=1
        return float(td)

    def episode(self):
        q=np.array(self.plan.rates).ravel();total=0.;tds=[];guide_count=0;explore_count=0
        epsilon=max(.05,.6*.965**self.episodes)
        guidance=self.request.guidance*.97**self.episodes
        for move in range(80):
            key,values=self.values(q)
            if self.rng.random()<guidance:action=self.teacher(q);guide_count+=1
            elif self.rng.random()<epsilon:action=int(self.rng.choice(self.admissible(q)));explore_count+=1
            else:
                valid=self.admissible(q);best=values[valid].max();action=int(self.rng.choice(valid[np.isclose(values[valid],best)]))
            new,reward,terminal=self.transition(q,action)
            if move==79 and not terminal:reward+=-3 if not self.observe(new)[4] else 0;terminal=True
            tds.append(abs(self.update(key,action,reward,new,terminal)));total+=reward;q=new
            if terminal:break
        self.episodes+=1
        record={'episode':self.episodes,'reward':total,'epsilon':epsilon,'guidance':guidance,
          'success':self.observe(q)[4],'volume':float(q.sum()*365),'active_bore_years':int(np.count_nonzero(q)),
          'moves':move+1,'td_error':float(np.mean(tds)),'updates':self.updates,'states':len(self.q),
          'guided_actions':guide_count,'exploratory_actions':explore_count,
          'last_action':int(action),'last_reward':float(reward),'last_state':key,
          'last_action_values':self.q.get(key,np.zeros(self.actions)).tolist()}
        self.history.append(record);self.history=self.history[-100:]
        return {'metrics':record,'rates':q.reshape(-1,self.plan.bore_count).tolist(),'history':self.history}

    def start_run(self):
        self.running=np.array(self.plan.rates).ravel();self.pending=None;self.run_moves=0;self.visited=set()
        return evaluate_plan(self.plan)

    def decision(self):
        if self.running is None:raise ValueError('Start the learned-policy run first')
        if self.pending is not None:return self.pending
        key,values=self.values(self.running);valid=self.admissible(self.running)
        ranked=sorted(valid,key=lambda a:values[a],reverse=True)
        # Evaluation never calls the teacher and never explores randomly.
        action=int(ranked[0]);q=self.trial(self.running,action)
        terminal=action==2*self.n or self.run_moves>=80 or tuple(q) in self.visited
        self.pending={'done':bool(terminal),'action':action,'well':int(action%self.n%self.plan.bore_count),
          'year':int((action%self.n)//self.plan.bore_count),'from_rate':float(self.running[action%self.n]),
          'to_rate':float(q[action%self.n]),'state':key,'q_values':values.tolist(),
          'reason':'Learned Q-policy: highest available action value' if not terminal else 'Policy stopped or repeated a design. Feasibility is reported separately.',
          'learning':False,'episodes':self.episodes}
        return self.pending

    def act(self):
        decision=self.decision()
        if decision['done']:return decision
        q,reward,_=self.transition(self.running,decision['action']);self.running=q;self.visited.add(tuple(q));self.run_moves+=1
        plan=self.plan.model_copy(update={'rates':q.reshape(-1,self.plan.bore_count).tolist(),'active_year':decision['year']})
        self.pending=None
        return {**decision,'reward':reward,'move':self.run_moves,'result':evaluate_plan(plan)}

SESSIONS=OrderedDict()
def new_session(request):
    agent=Agent(request);token=secrets.token_urlsafe(18);SESSIONS[token]=agent
    while len(SESSIONS)>8:SESSIONS.popitem(last=False)
    return {'session':token,'signature':agent.signature,'algorithm':'Tabular Q-learning','alpha':.2,'gamma':.95}
def get_agent(token):
    if token not in SESSIONS:raise ValueError('Learning session expired or server restarted. Start training again.')
    SESSIONS.move_to_end(token);return SESSIONS[token]
