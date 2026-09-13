import numpy as np
import pytest
from hydrofly.dashboard import drawdown_statistics
from hydrofly.mine_plan import MinePlan,evaluate_plan,simulation_frames,SimulationRequest,design_matrix,numerical,unit_costs


def test_contour_radius_interpolates_model_grid_and_flags_clipping():
    axis=np.array([-2.,0,2.]);x,y=np.meshgrid(axis,axis)
    dd=2-np.hypot(x,y)
    r=drawdown_statistics(0,-dd.ravel(),axis)
    assert r['max_drawdown_m']==2
    assert r['extent_m']==pytest.approx(1.)
    assert not r['extent_clipped']
    r=drawdown_statistics(0,np.full(9,-2.),axis)
    assert r['extent_clipped'] and r['extent_m']==pytest.approx(np.sqrt(8))
    zero=drawdown_statistics(0,np.zeros(9),axis)
    assert zero['extent_m']==zero['max_drawdown_m']==0


def test_plan_totals_peak_and_streamed_accumulation_match():
    p=MinePlan(bore_count=4,floors=[-375,-390],rates=[[700,300,50,0],[0,200,0,0]],conductivity=.1)
    result=evaluate_plan(p);s=result['statistics'];h=numerical(p,True)
    np.testing.assert_allclose(h,p.initial_head-design_matrix(p,True)@np.ravel(p.rates),atol=1e-8)
    assert s['max_drawdown_m']==pytest.approx(p.initial_head-h.min())
    assert s['pumped_volume_m3']==1250*365
    assert s['operating_cost_aud']==pytest.approx(365*np.sum(np.asarray(p.rates)*unit_costs(p)))
    frames=[]
    for start in range(0,25,6):frames.extend(simulation_frames(SimulationRequest(plan=p,start=start,count=6))['frames'])
    assert frames[0]['statistics']['pumped_volume_m3']==0
    assert frames[0]['statistics']['operating_cost_aud']==0
    assert frames[-1]['statistics']['operating_cost_aud']==pytest.approx(s['operating_cost_aud'])
    assert max(f['statistics']['max_drawdown_m'] for f in frames)==pytest.approx(s['max_drawdown_m'])
    assert max(f['statistics']['extent_m'] for f in frames)==pytest.approx(s['extent_m'])
    assert any(f['statistics']['extent_clipped'] for f in frames)==s['extent_clipped']


def test_narrow_cone_at_well_is_not_reported_as_zero_extent():
    r=drawdown_statistics(0,np.r_[-10.,np.zeros(9)],[-2.,0.,2.],grid_offset=1,extra_points=[[1.,0.]])
    assert r['extent_m']==1 and r['extent_underresolved']
    assert not r['extent_clipped']
