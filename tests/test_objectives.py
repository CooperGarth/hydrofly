import numpy as np
import pytest
from hydrofly.mine_plan import MinePlan,benchmark,numerical,objective_metric,unit_costs
from hydrofly.learning import Agent,LearningStart

def test_each_benchmark_minimises_its_selected_metric_with_targets():
    base=MinePlan()
    candidates={}
    for objective in ['rate','cost','drawdown']:
        p=base.model_copy(update={'objective':objective})
        r=benchmark(p)
        assert r['success'] and r['result']['feasible'] and r['result']['confined_valid']
        candidates[objective]=p.model_copy(update={'rates':r['result']['rates']})
    for objective,p in candidates.items():
        best=objective_metric(p,p.rates,numerical(p))
        for other in candidates.values():
            assert best<=objective_metric(p,other.rates,numerical(other))+1e-7
    assert not np.allclose(candidates['rate'].rates,candidates['cost'].rates)

def test_rewards_use_selected_objective_and_cost_units():
    for objective in ['rate','cost','drawdown']:
        p=MinePlan(objective=objective)
        agent=Agent(LearningStart(plan=p));q=np.array(p.rates).ravel()
        h,d,_,_,safe,loss=agent.observe(q)
        assert loss==pytest.approx(np.mean(d**2)+.05*objective_metric(p,q,h))
    p=MinePlan(objective='cost')
    from hydrofly.mine_plan import evaluate_plan
    r=evaluate_plan(p,grid=False)
    assert r['operating_cost_aud']==pytest.approx(sum(sum(np.array(row)*unit_costs(p))*365 for row in p.rates))

def test_lower_conductivity_delays_early_response_but_increases_late_drawdown():
    p=MinePlan(conductivity=.1,storativity=.001,rates=[[500.]*10 for _ in range(10)])
    assert p.conductivity==.1
    high=p.model_copy(update={'conductivity':.2})
    low_heads=numerical(p)[:,:25];high_heads=numerical(high)[:,:25]
    assert np.all(low_heads[-1]<high_heads[-1])
    assert np.any(low_heads[0]>high_heads[0])
