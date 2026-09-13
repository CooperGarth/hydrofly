import numpy as np
import pytest
from fastapi.testclient import TestClient
from hydrofly.api import app
from hydrofly.engine import Aquifer, evaluate, validate_rates
from hydrofly.agents import ConventionalPolicy, objective


def test_objective_normalisation():
    assert objective([0]*10,[100]*25)['score']==10000
    assert objective([6000]*10,[75]*25)['score']==1
    assert objective([0]*10,[50]*25)['score']==.02


def test_optimiser_feasible_and_better_than_full_pumping():
    r=ConventionalPolicy().optimise([2000]*10)
    assert r['success']
    solved=evaluate(r['rates'],grid=False)
    full=evaluate([6000]*10,grid=False)
    assert solved['feasible']
    assert solved['total_rate']<full['total_rate']
    assert objective(r['rates'],solved['control_heads'])['score']<objective(full['rates'],full['control_heads'])['score']
    assert len(r['trace'])>1


def test_infeasible_reported():
    r=ConventionalPolicy().optimise([0]*10,Aquifer(25,120,.02),.1)
    assert not r['success']
    assert 'infeasible' in r['message']


@pytest.mark.parametrize('q',[[0]*9,[float('nan')]*10,[-1]*10,[6001]*10])
def test_invalid_rates(q):
    with pytest.raises(ValueError):validate_rates(q)


def test_api_validation_and_health():
    client=TestClient(app)
    assert client.get('/api/health').json()['status']=='ok'
    assert len(client.get('/api/config').json()['wells'])==10
    for payload in [{'day':0},{'rates':[1]},{'conductivity':-2},{'extra':1},{'rates':[-1]*10}]:
        assert client.post('/api/evaluate',json=payload).status_code==422


def test_api_surface_is_python_model():
    client=TestClient(app);r=client.post('/api/evaluate',json={'rates':[0]*10})
    assert r.status_code==200
    d=r.json()
    np.testing.assert_allclose(d['surface'],100)
    assert d['score']==10000 and not d['feasible']
