import numpy as np
import pytest
from pydantic import ValidationError
from hydrofly.mine_plan import MinePlan,view_grid,evaluate_plan,simulation_frames,SimulationRequest

def test_low_k_and_regional_extent_return_finite_model_values():
    p=MinePlan(bore_count=4,floors=[-375],rates=[[1]*4],conductivity=.0001,view_extent=20000)
    r=evaluate_plan(p)
    assert r['axis'][0]==-20000 and r['axis'][-1]==20000
    assert np.isfinite(r['surface']).all()
    assert r['transmissivity']==pytest.approx(.02)
    frame=simulation_frames(SimulationRequest(plan=p,start=12,count=1))['frames'][0]
    np.testing.assert_allclose(frame['surface'],r['surface'])
    assert frame['head']==pytest.approx(r['timeline'][-1]['head'])

def test_wider_grid_preserves_central_sampling_and_heads():
    narrow,_=view_grid(2600);wide,_=view_grid(20000)
    assert set(narrow)<=set(wide)
    p=MinePlan(bore_count=4,floors=[-375],rates=[[500]*4],view_extent=2600)
    a=evaluate_plan(p);b=evaluate_plan(p.model_copy(update={'view_extent':20000}))
    ix=[b['axis'].index(v) for v in a['axis']]
    np.testing.assert_allclose(np.array(a['surface']),np.array(b['surface'])[np.ix_(ix,ix)],atol=1e-8)
    assert a['score']==pytest.approx(b['score'])
    with pytest.raises(ValidationError):MinePlan(conductivity=.00001)
