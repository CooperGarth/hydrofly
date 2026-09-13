import numpy as np
import pytest
from pydantic import ValidationError
from hydrofly.engine import build_model,heads,SUPERPIT
from hydrofly.mine_plan import MinePlan,numerical,benchmark,evaluate_plan
from hydrofly.learning import Agent,LearningStart

def test_annual_history_matches_direct_timflow_steps_and_recovery():
    p=MinePlan(bore_count=4,floors=[-375,-390],rates=[[700,400,100,0],[0,300,0,100]],active_year=1)
    m=build_model(p.aquifer(),p.wells(),[[(0,p.rates[0][i]),(365,p.rates[1][i])] for i in range(4)],tmax=730)
    times=np.arange(1,9)*365/4
    selected=times!=365  # Adapter deliberately rejects exact pumping-change times.
    direct=heads(m,SUPERPIT.controls,times[selected],p.aquifer()).T
    np.testing.assert_allclose(numerical(p)[selected,:25],direct,atol=2e-5,rtol=1e-7)
    first=build_model(p.aquifer(),p.wells(),[[(0,q)] for q in p.rates[0]],tmax=730)
    np.testing.assert_allclose(numerical(p)[3,:25],heads(first,SUPERPIT.controls,[365],p.aquifer())[:,0],atol=2e-5)
    reset=p.model_copy(update={'rates':[[0]*4,p.rates[1]]})
    assert np.max(abs(numerical(p)[-1]-numerical(reset)[-1]))>1

def test_plan_benchmark_checks_all_quarters():
    p=MinePlan();r=benchmark(p)
    assert r['success'] and r['result']['feasible'] and r['result']['confined_valid']
    assert all(max(y['quarter_heads'])<=y['target']+1e-5 for y in r['result']['years'])
    assert r['result']['total_volume']==pytest.approx(sum(y['total_rate']*365 for y in r['result']['years']))

def test_q_learning_bellman_update_and_seed_reproducibility():
    request=LearningStart(plan=MinePlan(bore_count=4,floors=[-375],rates=[[500]*4]),seed=7)
    a=Agent(request);q=np.array([500.]*4);key,values=a.values(q)
    a.update(key,0,1,q,True)
    assert values[0]==pytest.approx(.2)
    a=Agent(request);b=Agent(request)
    assert a.episode()==b.episode()
    assert a.updates>0 and any(np.any(v!=0) for v in a.q.values())
    a.start_run();old=a.running.copy();d=a.decision()
    np.testing.assert_array_equal(old,a.running)
    assert a.decision()==d
    if not d['done']:
        r=a.act();assert np.count_nonzero(old-a.running)<=1;assert r['result']['engine'].startswith('timflow')

def test_invalid_plan_rejected():
    with pytest.raises(ValidationError):MinePlan(bore_count=4)
    with pytest.raises(ValidationError):MinePlan(floors=[-390,-375],rates=[[0]*10]*2)

def test_learning_api_end_to_end_and_expired_session():
    from fastapi.testclient import TestClient
    from hydrofly.api import app
    from hydrofly.learning import SESSIONS
    p=MinePlan(bore_count=4,floors=[-375],rates=[[500]*4])
    with TestClient(app) as c:
        config=c.post('/api/learn/start',json={'plan':p.model_dump(),'seed':7})
        assert config.status_code==200
        body={'session':config.json()['session']}
        train=c.post('/api/learn/episode',json=body)
        assert train.status_code==200 and train.json()['metrics']['updates']>0
        assert c.post('/api/learn/run',json=body).status_code==200
        decision=c.post('/api/learn/decide',json=body)
        assert decision.status_code==200 and decision.json()['learning'] is False
        exported=c.post('/api/learn/export',json=body).json()
        assert exported['episodes']==1 and exported['q_table']
        SESSIONS.pop(body['session'])
        assert c.post('/api/learn/episode',json=body).status_code==422
