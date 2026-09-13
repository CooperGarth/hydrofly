import numpy as np
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient
from hydrofly.api import app
from hydrofly.engine import SUPERPIT, build_model, heads, response, evaluate
from hydrofly.fly import Strategy, FlyState, decide


def test_superpit_reference_and_independent_multiwell_model():
    v=SUPERPIT
    assert (v.rim_rx*2,v.rim_ry*2,v.crest-v.floor,v.target)==(3780,1610,750,-395)
    q=np.arange(1,11)*100.
    direct=build_model(v.aquifer,v.wells,[[(0,float(rate))] for rate in q])
    expected=heads(direct,v.controls,[v.day],v.aquifer)[:,0]
    actual=v.aquifer.initial_head-response(v.aquifer,v.day,False,v)@q
    np.testing.assert_allclose(actual,expected,atol=1e-7,rtol=1e-8)


def test_fly_reaches_target_through_single_well_actions():
    v=SUPERPIT;q=[0.]*10;state=FlyState();safe=False
    for _ in range(201):
        action=decide(q,v.aquifer,v.day,v,state=state)
        if action['done']:break
        old=np.array(q);q[action['well']]=action['to_rate']
        assert np.count_nonzero(old!=q)==1
        result=evaluate(q,v.aquifer,v.day,level=v)
        assert result['confined_valid_at_samples']
        if safe: assert result['feasible'] and sum(q)<old.sum()
        safe=result['feasible'];state=FlyState(**action['state'])
    else:pytest.fail('Fly failed to stop within budget')
    assert safe
    assert result['total_rate']==pytest.approx(5343.75)


def test_patrol_order_and_budget_are_user_controlled():
    v=SUPERPIT
    strategy=Strategy(search='patrol',well_order=list(range(10,0,-1)),max_moves=1)
    q=[0.]*10;a=decide(q,v.aquifer,v.day,v,strategy)
    assert a['well']==9 and q==[0.]*10  # decision does not mutate rates
    assert a['to_rate']==500
    assert decide(q,v.aquifer,v.day,v,strategy,FlyState(**a['state']))['done']
    with pytest.raises(ValidationError):Strategy(well_order=[1]*10)
    with pytest.raises(ValidationError):Strategy(minimum_step=1000,step=500)


def test_api_decision_then_action():
    v=SUPERPIT
    payload={'level':'superpit','rates':[0.]*10,'day':365,'conductivity':.2,'thickness':200,
             'storativity':.001,'strategy':{'search':'patrol'},'state':{}}
    with TestClient(app) as client:
        decision=client.post('/api/fly/decide',json=payload)
        assert decision.status_code==200
        assert 'result' not in decision.json()
        applied=client.post('/api/fly/act',json=payload)
        assert applied.status_code==200
        data=applied.json()
        assert data['well']==decision.json()['well']
        assert np.count_nonzero(data['result']['rates'])==1
        assert data['result']['worst_head']==pytest.approx(decision.json()['predicted_worst_head'])
        assert len(data['result']['surface'])==35
        assert client.post('/api/fly/decide',json={**payload,'strategy':{'search':'arbitrary code'}}).status_code==422
