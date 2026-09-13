"""Reproducible training evidence, not a claim of generalisation."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from hydrofly.learning import Agent,LearningStart
from hydrofly.mine_plan import MinePlan,benchmark,evaluate_plan

p=MinePlan();agent=Agent(LearningStart(plan=p,seed=42))
for _ in range(30):agent.episode()
agent.start_run()
for _ in range(81):
    if agent.decision()['done']:break
    agent.act()
learned=p.model_copy(update={'rates':agent.running.reshape(-1,p.bore_count).tolist()})
r=evaluate_plan(learned);b=benchmark(p)
evidence={'seed':42,'episodes':30,'first_ten_successes':sum(x['success'] for x in agent.history[:10]),
 'last_ten_successes':sum(x['success'] for x in agent.history[-10:]),'q_updates':agent.updates,
 'learned_policy_feasible':r['feasible'],'learned_policy_volume':r['total_volume'],
 'lp_volume':b['result']['total_volume'],'history':agent.history,
 'scope':'Same-plan evaluation; teacher disabled; one seed. No out-of-distribution or global-optimality claim.'}
Path('artifacts/learning.json').write_text(json.dumps(evidence,indent=2))
fig,axs=plt.subplots(1,3,figsize=(15,4),layout='constrained')
axs[0].plot([x['episode'] for x in agent.history],[x['reward'] for x in agent.history],color='#286b62')
axs[0].set(xlabel='Training episode',ylabel='Episode reward',title='Actual Q-learning rewards / seed 42')
for row,label in [(r['years'],'Learned policy'),(b['result']['years'],'LP volume benchmark')]:axs[1].plot([x['year'] for x in row],[x['total_rate'] for x in row],marker='o',label=label)
axs[1].set(xlabel='Plan year',ylabel='Total pumping (m³/day)',title='Policy evaluation: quarterly constraints');axs[1].legend(fontsize=8)
image=axs[2].contourf(r['axis'],r['axis'],r['surface'],levels=15,cmap='viridis')
axs[2].scatter(*np.array(r['wells']).T,c='white',edgecolors='black',s=20)
axs[2].set(xlabel='x (m)',ylabel='y (m)',title='Year 1 end head / actual timflow');fig.colorbar(image,ax=axs[2],label='Head (m AHD)')
fig.savefig('artifacts/learning-diagnostic.png',dpi=150)
print({k:v for k,v in evidence.items() if k!='history'})
