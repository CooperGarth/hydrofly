import numpy as np
import pytest
from hydrofly.engine import build_model,heads,SUPERPIT
from hydrofly.mine_plan import MinePlan,SimulationRequest,simulation_frames,numerical,floor_at,benchmark,GRID

def test_ten_year_stream_matches_direct_timflow_including_previous_years():
    p=MinePlan(bore_count=4,rates=[[500+20*y,200 if y<5 else 0,100,0] for y in range(10)])
    result=simulation_frames(SimulationRequest(plan=p,start=119,count=2))
    assert result['done'] and result['next']==121
    assert result['frames'][-1]['day']==3650
    m=build_model(p.aquifer(),p.wells(),[[(y*365,p.rates[y][i]) for y in range(10)] for i in range(4)],tmax=3650)
    pts=np.vstack((SUPERPIT.controls,GRID[[0,312,624]]))
    direct=heads(m,pts,[f['day'] for f in result['frames']],p.aquifer())
    for j,frame in enumerate(result['frames']):
        assert frame['head']==pytest.approx(direct[:25,j].max(),abs=2e-5)
        np.testing.assert_allclose(np.asarray(frame['surface']).ravel()[[0,312,624]],direct[25:,j],atol=2e-5)
    assert result['frames'][-1]['volume_to_date']==sum(map(sum,p.rates))*365

def test_day_zero_and_batch_boundary_do_not_reset_pumping_history():
    p=MinePlan(bore_count=4,floors=[-375,-390],rates=[[500]*4,[0]*4])
    first=simulation_frames(SimulationRequest(plan=p,start=0,count=1))['frames'][0]
    assert first['head']==-365 and first['floor']==-350 and first['volume_to_date']==0
    assert np.all(np.array(first['surface'])==-365)
    a=simulation_frames(SimulationRequest(plan=p,start=11,count=3))['frames']
    b=simulation_frames(SimulationRequest(plan=p,start=13,count=1))['frames'][0]
    assert a[-1]==b
    assert b['head']==pytest.approx(numerical(p)[12,:25].max())
    assert b['head']<-365
    assert floor_at(p,182.5)==-350
    assert floor_at(p,365-1e-6)==-350
    assert floor_at(p,365)==-375
    assert floor_at(p,365+1e-6)==-375
    assert floor_at(p,730)==-390
    from hydrofly.mine_plan import target_heads
    target=target_heads(p)
    assert target[10]==-355 and target[11]==-380
    assert target[22]==-380 and target[23]==-395

def test_impossible_initial_clearance_is_not_declared_feasible():
    p=MinePlan(initial_floor=-370)
    assert not benchmark(p)['success']
    assert not simulation_frames(SimulationRequest(plan=p,count=1))['frames'][0]['feasible']
