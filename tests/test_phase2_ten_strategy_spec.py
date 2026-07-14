import copy
from lab.phase2_execution import sha
from lab.phase2_ten_strategy import coverage_matrix, fixture_suite, strategy_suite


def test_suite_is_exactly_the_committed_two_families_and_nonsearchable():
    suite=strategy_suite(); strategies=suite["strategies"]
    assert suite["schema_version"]=="nora.phase2_ten_strategy_suite_v1" and len(strategies)==10
    assert sum(x["family"]=="trend-pullback" for x in strategies)==5
    assert sum(x["family"]=="close-confirmed breakout" for x in strategies)==5
    assert [x["strategy_identifier"] for x in strategies]==[f"trend_pullback_{i}" for i in range(1,6)]+[f"close_breakout_{i}" for i in range(1,6)]
    assert all(not x["searchable"] and not x["grammar_admitted"] for x in strategies)
    assert not suite["searchable"] and not suite["grammar_admitted"] and not suite["phase2_complete"]


def test_all_dependencies_are_accepted_and_breakout_shift_is_completed():
    suite=strategy_suite()
    accepted={"layer1.ema","layer1.atr","layer1.highest","layer1.lowest","transform.cross","transform.slope","transform.distance_atr"}
    for strategy in suite["strategies"]:
        assert set(strategy["indicator_node_identities"])<=accepted
        assert strategy["entry_rule"]["timing"]=="next_open"
        assert strategy["execution"]["precedence"]==["gap","signal","time","intrabar"]
        if strategy["family"]=="close-confirmed breakout":assert strategy["parameters"]["completed_level_shift"]==1


def test_every_decision_relevant_mutation_changes_strategy_and_suite_identity():
    suite=strategy_suite();base=suite["strategies"][0]
    paths=[("family","x"),("direction_support",["short"]),("parameters",{"period":99}),("entry_ast",{"schema_version":1,"root":{"kind":"boolean_series","ref":{"series":"x","type":"boolean"}}}),("entry_rule",{"timing":"same_bar"}),("exit_rule",{"kind":"x"}),("time_session_rule",{"declared_contract":"x"}),("friday_close",{"enabled":False}),("brackets",{"stop_atr_multiple":2.0}),("execution",{"contract":"x"}),("null_warmup","x"),("expected_no_trade_conditions",[]) ]
    for key,value in paths:
        changed=copy.deepcopy(base);changed.pop("strategy_identity");changed[key]=value
        assert sha(changed)!=base["strategy_identity"]
    changed=copy.deepcopy(suite);changed.pop("suite_identity");changed["strategies"]=list(reversed(changed["strategies"]))
    assert sha(changed)!=suite["suite_identity"]


def test_fixture_and_coverage_contracts_are_complete_and_deterministic():
    one=fixture_suite();two=fixture_suite();coverage=coverage_matrix()
    assert one==two and len(one["segments"])==10
    assert set(one["required_coverage"])==set(one["coverage_owners"])
    assert coverage["input_fixture_identity"]==one["input_fixture_identity"]
