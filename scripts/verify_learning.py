"""Reproducible same-plan learning diagnostic, not a generalisation study."""
import argparse,json,time
from pathlib import Path
import numpy as np
from hydrofly.learning import Agent,LearningStart
from hydrofly.mine_plan import MinePlan,benchmark,objective_metric


def summary(agent,rates):
    h,d,_,_,safe,score=agent.observe(rates)
    return dict(feasible=safe,score=score,objective=objective_metric(agent.plan,rates,h),
                volume_m3=float(rates.sum()*365),maximum_target_exceedance_m=float(max(0,(h[:,:25]-agent.targets).max())),
                minimum_head_m=float(h.min()))


def policy_run(agent):
    agent.running=np.array(agent.plan.rates).ravel();agent.pending=None;agent.run_moves=0;agent.visited=set()
    weights=agent.weights.copy()
    for _ in range(agent.request.max_moves+1):
        d=agent.decision()
        if d['done']:break
        q,_,_=agent.transition(agent.running,d['action'])
        agent.running=q;agent.visited.add(tuple(q));agent.run_moves+=1;agent.pending=None
    np.testing.assert_array_equal(weights,agent.weights)
    return {**summary(agent,agent.running),'moves':agent.run_moves}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--episodes',type=int,default=8)
    parser.add_argument('--seeds',type=int,nargs='+',default=[7,42,91]);parser.add_argument('--objective',default='rate',choices=['rate','cost','drawdown'])
    parser.add_argument('--output',default='docs/learning-verification.json');args=parser.parse_args()
    plan=MinePlan(rates=[[500.]*10]*10,objective=args.objective)
    ref=benchmark(plan,grid=False)
    report={'plan':plan.model_dump(),'episodes_per_seed':args.episodes,'moves_per_episode':200,
            'scope':'Same ten-year plan; frozen learned weights, no teacher, model-based improvement safeguard remains active.',
            'benchmark':{k:ref['result'][k] for k in ['feasible','objective','total_volume','score']},'seeds':[]}
    untrained=Agent(LearningStart(plan=plan,max_moves=200));report['initial']=summary(untrained,untrained.best)
    report['untrained_safeguarded_policy']=policy_run(untrained)
    for seed in args.seeds:
        start=time.perf_counter();a=Agent(LearningStart(plan=plan,seed=seed,max_moves=200));best_ranks=[]
        for _ in range(args.episodes):
            a.episode();best_ranks.append(a.rank(a.best))
        assert all(y<=x for x,y in zip(best_ranks,best_ranks[1:]))
        row={'seed':seed,'best_guided_plan':summary(a,a.best),'frozen_safeguarded_policy':policy_run(a),
             'updates':a.updates,'weights':a.weights.tolist(),'seconds':time.perf_counter()-start}
        report['seeds'].append(row);Path(args.output).write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(row),flush=True)

if __name__=='__main__':main()
