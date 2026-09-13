"""Learning correctness gates; performance evidence lives in a separate diagnostic."""
import json
import numpy as np
from hydrofly.learning import Agent, LearningStart
from hydrofly.mine_plan import MinePlan
from hydrofly.portable import Checkpoint, checkpoint, restore


def test_exact_schedule_identity_and_shared_values():
    a=Agent(LearningStart(plan=MinePlan(bore_count=4,floors=[-375],rates=[[500]*4])))
    q=a.best.copy();other=q.copy();other[0]+=1
    assert a.state(q)!=a.state(other)
    key,_=a.values(q);before=a.values(other)[1].copy()
    a.update(key,0,1,q,True)
    assert not np.array_equal(a.values(other)[1],before)


def test_incumbent_survives_exploration_and_portable_resume():
    a=Agent(LearningStart(plan=MinePlan(),max_moves=20))
    original=a.rank(a.best)
    for _ in range(3):
        result=a.episode()
        assert a.rank(a.best)<=original
        np.testing.assert_array_equal(np.ravel(result['rates']),a.best)
        assert 'experiment_rates' in result
        restored=restore(Checkpoint.model_validate(json.loads(json.dumps(checkpoint(a)))))
        np.testing.assert_array_equal(restored.best,a.best)
        np.testing.assert_array_equal(restored.weights,a.weights)
        a=restored


def test_learnt_evaluation_does_not_update_weights_or_use_teacher():
    a=Agent(LearningStart(plan=MinePlan(bore_count=4,floors=[-375],rates=[[500]*4]),max_moves=20))
    a.episode();weights=a.weights.copy();updates=a.updates
    def forbidden(*args):raise AssertionError('Teacher called during policy evaluation')
    a.teacher=forbidden;a.start_run();a.decision();a.act()
    np.testing.assert_array_equal(a.weights,weights)
    assert a.updates==updates


def test_backtracking_preserves_feasible_targets():
    a=Agent(LearningStart(plan=MinePlan(),max_moves=20))
    assert a.observe(a.best)[4]
    changed=[]
    for action in a.admissible(a.best):
        trial=a.trial(a.best,action)
        assert a.observe(trial)[4]
        delta=np.max(abs(trial-a.best))
        if delta:changed.append(delta)
    # Binding constraints must be respected even with a large requested step.
    assert all(delta<=a.request.step for delta in changed)


def test_training_rejects_unreachable_day_zero_and_invalid_start():
    import pytest
    from hydrofly.portable import handle,PortableRequest
    for plan,message in [(MinePlan(initial_head=-340),'Day 0'),
                         (MinePlan(rates=[[6000]*10]*10),'confined aquifer roof')]:
        with pytest.raises(ValueError,match=message):
            handle(PortableRequest(operation='start',request=LearningStart(plan=plan)))


def test_trained_safeguarded_policy_meets_a_feasible_plan():
    plan=MinePlan(bore_count=4,floors=[-375],rates=[[500]*4],objective='rate',conductivity=.1)
    a=Agent(LearningStart(plan=plan,max_moves=100,seed=42))
    assert not a.observe(a.best)[4]
    for _ in range(3):a.episode()
    a.running=np.array(plan.rates).ravel();a.run_moves=0;a.visited=set();a.pending=None
    for _ in range(101):
        decision=a.decision()
        if decision['done']:break
        a.running,_,_=a.transition(a.running,decision['action'])
        a.visited.add(tuple(a.running));a.run_moves+=1;a.pending=None
    assert a.observe(a.running)[4]


def test_feature_cache_eviction_does_not_discard_learning_or_break_update():
    a=Agent(LearningStart(plan=MinePlan(bore_count=4,floors=[-375],rates=[[500]*4])))
    q=a.best.copy();key,_=a.values(q)
    for rate in [501.,502.,503.]:a.values(np.full(4,rate))
    # The next-state calculation evicts the old feature matrix, not its update.
    a.update(key,0,1,np.full(4,504.),False)
    assert np.any(a.weights!=0)
