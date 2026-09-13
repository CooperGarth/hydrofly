"""Independent solution checks. AnaFlow is a test dependency only."""
import numpy as np
import pytest
from anaflow import theis
from scipy.special import exp1
from hydrofly.engine import Aquifer, build_model, heads, WELLS, CONTROL_POINTS, response


@pytest.mark.parametrize("k,b,s", [(10,80,.001), (2,30,.02), (25,100,.0001)])
def test_single_well_against_anaflow(k,b,s):
    aq = Aquifer(k,b,s)
    times = np.array([.1,1,10,30,100])
    radii = np.array([10.,100.,500.])
    # Shrink the finite-radius timflow well for a line-source Theis comparison.
    m = build_model(aq, [[0,0]], [[(0,1000)]],well_radius=1e-4)
    actual = heads(m, np.column_stack((radii,np.zeros(3))),times,aq) - aq.initial_head
    reference = theis(time=times,rad=radii,transmissivity=k*b,storage=s,rate=-1000).T
    np.testing.assert_allclose(actual,reference,rtol=2e-5,atol=2e-6)


def test_published_theis_dimensionless_solution():
    # Theis (1935): s=Q/(4*pi*T)*E1(u), u=r²*S/(4*T*t).
    # Independent test oracle only; production always uses timflow.
    aq=Aquifer(); m=build_model(aq,[[0,0]],[[(0,1000)]])
    u=100**2*aq.storativity/(4*aq.transmissivity*1)
    expected=1000/(4*np.pi*aq.transmissivity)*exp1(u)
    assert aq.initial_head-heads(m,[[100,0]],[1],aq)[0,0] == pytest.approx(expected,rel=2e-6)


def test_multiwell_superposition_and_response_matrix():
    aq=Aquifer(); q=np.linspace(700,3100,10)
    combined=build_model(aq,WELLS,[[(0,float(x))] for x in q])
    direct=heads(combined,CONTROL_POINTS,[30],aq)[:,0]
    basis=aq.initial_head-response(aq,30,False)@q
    np.testing.assert_allclose(direct,basis,rtol=0,atol=3e-6)


def test_pumping_change_and_recovery():
    aq=Aquifer(); times=np.array([1.,9.,11.,20.,40.]);r=100.
    m=build_model(aq,[[0,0]],[[(0,1000),(10,0)]])
    actual=heads(m,[[r,0]],times,aq)[0]-aq.initial_head
    ref=theis(time=times,rad=[r],transmissivity=800,storage=.001,rate=-1000)[:,0]
    after=times>10
    ref[after]+=theis(time=times[after]-10,rad=[r],transmissivity=800,storage=.001,rate=1000)[:,0]
    np.testing.assert_allclose(actual,ref,rtol=2e-5,atol=2e-6)
    assert actual[-1]>actual[-2]


def test_zero_rate_symmetry_and_time_limits():
    aq=Aquifer();zero=build_model(aq,[[0,0]],[[(0,0)]])
    np.testing.assert_allclose(heads(zero,[[100,0]],[1,30]),100)
    m=build_model(aq,[[0,0]],[[(0,1000)]])
    np.testing.assert_allclose(heads(m,[[100,0],[-100,0],[0,100]],[1]),heads(m,[[100,0]],[1])[0,0])
    for time in [0,500,float('nan')]:
        with pytest.raises(ValueError):heads(m,[[100,0]],[time])


def test_invalid_aquifer_and_schedules():
    with pytest.raises(ValueError):Aquifer(storativity=0)
    with pytest.raises(ValueError):build_model(wells=[[0,0]],schedules=[[(1,100)]])
    with pytest.raises(ValueError):build_model(wells=[[0,0]],schedules=[[(0,100),(0,200)]])


def test_finite_well_radius_converges_to_line_source():
    aq=Aquifer(2,30,.02)
    ref=float(theis(time=[.1],rad=[10],transmissivity=60,storage=.02,rate=-1000)[0,0])
    errors=[]
    for radius in [.15,.015,.0015]:
        m=build_model(aq,[[0,0]],[[(0,1000)]],well_radius=radius)
        errors.append(abs(heads(m,[[10,0]],[.1],aq)[0,0]-aq.initial_head-ref))
    assert errors[0] < .0004
    assert errors[2] < errors[1] < errors[0]


def test_reject_evaluation_at_or_too_close_to_pumping_step():
    m=build_model(wells=[[0,0]],schedules=[[(0,1000),(10,0)]])
    for t in [10,10.0001]:
        with pytest.raises(ValueError): heads(m,[[100,0]],[t])
