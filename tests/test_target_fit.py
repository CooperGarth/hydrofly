import numpy as np
import pytest
from hydrofly.mine_plan import MinePlan,numerical,evaluate_plan,benchmark
from hydrofly.learning import Agent,LearningStart

def test_demo_preset_meets_targets_and_improves_tracking():
    p=MinePlan();r=evaluate_plan(p,grid=False)
    assert p.initial_head==-355 and p.conductivity==.05 and p.storativity==.01
    assert r['feasible'] and r['confined_valid']
    slack=np.array([t['target']-t['head'] for t in r['timeline']])
    assert slack.min()>=-1e-5
    assert slack.mean()<4.4
    lowered=np.array([t['target']<p.initial_head for t in r['timeline']])
    assert slack[lowered].min()>=.0099
    base=benchmark(p.model_copy(update={'conductivity':.1,'storativity':.001}),grid=False)['result']
    old=np.mean([t['target']-t['head'] for t in base['timeline']])
    assert slack.mean()<old*.85

def test_initial_head_is_used_consistently_by_model_and_agent():
    p=MinePlan(bore_count=4,floors=[-375],rates=[[500]*4])
    higher=p.model_copy(update={'initial_head':p.initial_head+4})
    np.testing.assert_allclose(numerical(higher)-numerical(p),4,atol=1e-8)
    agent=Agent(LearningStart(plan=higher))
    np.testing.assert_allclose(agent.observe(np.array(higher.rates).ravel())[0],numerical(higher))
    assert not evaluate_plan(higher,grid=False)['feasible'] # Day-zero target is missed.
    assert not benchmark(higher,grid=False)['success']
