import json
import numpy as np
import pytest
from pydantic import ValidationError
from hydrofly.learning import Agent,LearningStart
from hydrofly.mine_plan import MinePlan
from hydrofly.portable import Checkpoint,PortableRequest,handle,restore

def test_checkpoint_survives_fresh_worker_and_preserves_random_state():
    request=LearningStart(plan=MinePlan(bore_count=4,floors=[-375],rates=[[500]*4]),seed=12)
    original=Agent(request)
    state=handle(PortableRequest(operation='start',request=request))['checkpoint']
    for _ in range(3):
        response=handle(PortableRequest(operation='episode',checkpoint=Checkpoint.model_validate(json.loads(json.dumps(state)))))
        assert response['value']==original.episode()
        state=response['checkpoint']
    resumed=restore(Checkpoint.model_validate(state))
    assert resumed.episodes==3
    np.testing.assert_array_equal(resumed.rng.integers(0,999,10),original.rng.integers(0,999,10))
    assert len(json.dumps(state))<4_000_000

def test_run_decide_act_can_move_between_workers():
    request=LearningStart(plan=MinePlan(bore_count=4,floors=[-375],rates=[[500]*4]))
    state=handle(PortableRequest(operation='start',request=request))['checkpoint']
    state=handle(PortableRequest(operation='run',checkpoint=Checkpoint.model_validate(state)))['checkpoint']
    decision=handle(PortableRequest(operation='decide',checkpoint=Checkpoint.model_validate(state)))
    action=handle(PortableRequest(operation='act',checkpoint=Checkpoint.model_validate(decision['checkpoint'])))
    assert action['value']['action']==decision['value']['action']
    assert action['checkpoint']['run_moves']==1
    assert np.count_nonzero(np.array(action['checkpoint']['running'])-state['running'])==1

def test_malformed_q_and_rates_are_rejected():
    start=handle(PortableRequest(operation='start',request=LearningStart(plan=MinePlan())))['checkpoint']
    with pytest.raises(ValidationError):Checkpoint.model_validate({**start,'q':{'bad':[float('nan')]}})
    with pytest.raises(ValidationError):Checkpoint.model_validate({**start,'running':[-1]*30})
