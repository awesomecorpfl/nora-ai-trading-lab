import copy
from lab.phase2_time_contracts import contracts, identity

def test_contracts_are_deterministic_and_sensitive():
    base=contracts(); assert base==contracts()
    keys={"dataset":"dataset_clock_identity","strategy":"strategy_clock_identity","session":"session_clock_identity","anchoring":"anchoring_identity","reasons":"reason_code_identity"}
    for section in keys:
        item=copy.deepcopy(base[section]); key=keys[section]; original=item.pop(key)
        assert original==identity(item)
        for field in list(item):
            changed=copy.deepcopy(item); changed[field]=str(changed[field])+"-mutated"
            assert identity(changed)!=original

def test_broker_contract_is_dst_following_not_permanent_offset():
    value=contracts(); assert value["dataset"]["timezone_identity"]=="america_new_york_plus_7_v1"
    assert value["dataset"]["dst_regime_identity"]=="new_york_dst_v1"
    assert value["dst_regime"]["broker_adjustment_seconds"]==25200
