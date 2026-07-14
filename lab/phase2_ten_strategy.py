"""Frozen ten-strategy Phase-2 parity suite and deterministic fixture contracts."""
from __future__ import annotations

import copy
import json
import subprocess
import tempfile
from pathlib import Path

from lab.phase2_execution import sha
from lab.phase2_layer1_inventory import dependency_map, matrix

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests/fixtures/phase2_ten_strategy_suite"
SCHEMA = "nora.phase2_ten_strategy_suite_v1"
EXECUTION_IDENTITY = "2e8312d5a1ffca744f916982376cfab6fec2c167b1d349b749fe09b057252029"
TIME_IDENTITY = "fd15de7bb0631131cfa530e7caf3594b8ee6a34b1b7b021d1ba15b9c0afc3621"
LAYER1_ACCEPTANCE = "3fe6ce82622ad0a0fa01e887e4745a02bfcb8e1ff5e0899f37e3108e50687cdb"
LEDGER_FIELDS = ["strategy_identity","trade_ordinal","direction","signal_index","signal_timestamp",
                 "entry_index","entry_timestamp","entry_price","initial_stop","initial_target",
                 "exit_index","exit_timestamp","exit_price","exit_reason","holding_bars","gross_price_return",
                 "no_trade_reason","terminal_source_disposition"]


def identified(value: dict, field: str) -> dict:
    result = copy.deepcopy(value)
    result[field] = sha(value)
    return result


def _ast(family: str, side: str, period: int, threshold: float | None = None) -> dict:
    direction = "above" if side == "long" else "below"
    if family == "trend-pullback":
        slope_op = "gt" if side == "long" else "lt"
        return {"schema_version": 1, "root": {"kind": "and", "args": [
            {"kind": "boolean_series", "ref": {"series": f"close_ema_cross_{direction}", "type": "boolean"}},
            {"kind": "compare", "op": slope_op, "left": {"kind": "numeric_series", "ref": {"series": "ema_slope", "type": "numeric"}}, "right": {"kind": "number", "value": 0.0}},
            {"kind": "compare", "op": "lte", "left": {"kind": "numeric_series", "ref": {"series": "distance_atr_abs", "type": "numeric"}}, "right": {"kind": "number", "value": threshold}},
        ]}}
    level = "highest_shift_1" if side == "long" else "lowest_shift_1"
    return {"schema_version": 1, "root": {"kind": "boolean_series", "ref": {"series": f"close_{level}_cross_{direction}", "type": "boolean"}}}


def strategy_suite() -> dict:
    dep = dependency_map()
    nodes = {x["canonical_id"]: x["canonical_identity"] for x in matrix()["nodes"]}
    strategies = []
    for order, design in enumerate(dep["strategies"], 1):
        side = design["side"]
        family = design["family"]
        period = design.get("ema_period", design.get("period"))
        params = {"period": period}
        if family == "trend-pullback":
            params.update({"slope_lookback": 1, "distance_atr_limit": design["distance_atr_limit"], "atr_period": 3})
            exit_rule = {"kind": "opposite_cross_or_time", "maximum_holding_bars": 3 if order % 2 else 2}
        else:
            params.update({"completed_level_shift": design["completed_level_shift"]})
            exit_rule = {"kind": "opposite_level_cross_or_time", "maximum_holding_bars": 2 if order % 2 else 3}
        rule = {
            "schema_version": "nora.phase2_strategy_spec_v1", "strategy_identifier": design["id"],
            "suite_order": order, "family": family, "direction_support": [side],
            "indicator_node_identities": {n: nodes[n] for n in design["nodes"]},
            "parameters": params, "entry_ast": _ast(family, side, period, design.get("distance_atr_limit")),
            "completed_bar_signal_semantics": "decision_on_closed_bar_source_i; terminal source is not executable",
            "shift_indexing": "oldest_to_newest; decision i; completed breakout level window ends i-1",
            "entry_rule": {"timing": "next_open", "position_policy": "one_position_no_overlap", "repeated_true": "edge_only"},
            "exit_rule": exit_rule,
            "time_session_rule": {"declared_contract": TIME_IDENTITY, "session": "fixture_declared_session", "rollover_filter": order in (2, 7), "monday_delay": order in (5, 10)},
            "friday_close": {"enabled": True, "precedence": "signal_before_friday_time"},
            "brackets": {"stop_atr_multiple": 1.0, "target_atr_multiple": 1.5},
            "execution": {"contract": EXECUTION_IDENTITY, "precedence": ["gap","signal","time","intrabar"], "gap": "fill_trigger_at_open", "dual_touch": "pessimistic_stop", "same_bar_entry_exit": False},
            "null_warmup": "any unavailable dependency suppresses signal",
            "trade_ledger_schema": "nora.phase2_strategy_trade_ledger_v1",
            "expected_no_trade_conditions": ["warmup_or_null", "outside_session", "rollover", "monday_delay", "position_open", "terminal_source"],
            "grammar_admitted": False, "searchable": False,
        }
        strategies.append(identified(rule, "strategy_identity"))
    families = {}
    for family in ("trend-pullback", "close-confirmed breakout"):
        members = [x["strategy_identity"] for x in strategies if x["family"] == family]
        families[family] = sha({"schema_version": "nora.phase2_strategy_family_plan_v1", "family": family, "members": members})
    ledger = identified({"schema_version": "nora.phase2_strategy_trade_ledger_v1", "fields": LEDGER_FIELDS,
                         "ordering": ["suite_order","trade_ordinal"], "numeric_null": "JSON null"}, "strategy_ledger_schema_identity")
    reasons = identified({"schema_version": "nora.phase2_strategy_reason_codes_v1", "exit": ["gap_stop","gap_target","signal_exit","friday_close","time_exit","stop","target","pessimistic_dual_touch"],
                          "no_trade": ["none","warmup_or_null","outside_session","rollover","monday_delay","terminal_source"]}, "strategy_reason_vocabulary_identity")
    value = {"schema_version": SCHEMA, "dependency_map_identity": dep["dependency_map_identity"],
             "layer1_matrix_identity": matrix()["matrix_identity"], "layer1_acceptance_identity": LAYER1_ACCEPTANCE,
             "execution_contract_identity": EXECUTION_IDENTITY, "time_rule_contract_identity": TIME_IDENTITY,
             "strategies": strategies, "family_plan_identities": families, "ledger_schema": ledger,
             "reason_vocabulary": reasons, "grammar_admitted": False, "searchable": False, "phase2_complete": False}
    return identified(value, "suite_identity")


def fixture_suite() -> dict:
    # Each segment is isolated and deterministic. Signal indices are derived by the Rust/MQL5 runtimes;
    # the purpose tags are coverage assertions, never resolver inputs.
    segments = []
    for index, strategy in enumerate(strategy_suite()["strategies"]):
        base = 100.0 + index * 20.0
        side = strategy["direction_support"][0]
        offsets=[0,-1,-2,-1,2,4,3,6,2,1,8,10,5,3,9,4]
        closes=[base+x if side=="long" else base-x for x in offsets]
        bars=[]
        for row, close in enumerate(closes):
            open_=close + (-0.5 if side == "long" else 0.5)
            span=2.0 if row in (6,8) else 1.0
            bars.append({"timestamp":f"2040-01-{index+1:02d} {row:02d}:00","open":open_,"high":max(open_,close)+span,"low":min(open_,close)-span,"close":close,
                         "session_member": row!=0 and not (index==1 and row==4), "friday_close": row==12 and index in (2,7), "rollover":row==4 and strategy["time_session_rule"]["rollover_filter"],
                         "monday_delay":row==4 and strategy["time_session_rule"]["monday_delay"]})
        segment={"fixture_identifier":f"fixture_{strategy['strategy_identifier']}","strategy_identity":strategy["strategy_identity"],"bars":bars,
                 "coverage_tags":["long_entry" if side=="long" else "short_entry","null_warmup_suppression","next_open_entry","session_filtering","terminal_source_not_executed","no_overlap"]}
        segments.append(identified(segment,"fixture_identity"))
    required=["long_entry","short_entry","no_trade_result","repeated_true_signals","null_warmup_suppression","next_open_entry","gap_entry","signal_exit","time_exit","friday_close_exit","stop_exit","target_exit","pessimistic_dual_touch","terminal_source_not_executed","session_filtering","rollover_filtering","monday_delay_filtering","completed_level_shift","multiple_sequential_trades","no_overlap"]
    # Coverage ownership is frozen here and verified against Rust outcomes later.
    owners={name:[segments[i % 10]["fixture_identifier"]] for i,name in enumerate(required)}
    accepted_execution_coverage={
        "next_open_entry":"completed_next_open","gap_entry":"gap_target","signal_exit":"signal_exit",
        "time_exit":"time_exit","stop_exit":"nonambiguous_stop","target_exit":"nonambiguous_target",
        "pessimistic_dual_touch":"pessimistic_dual_touch","terminal_source_not_executed":"entry_row_excluded_terminal",
        "no_overlap":"completed_next_open"
    }
    value={"schema_version":"nora.phase2_ten_strategy_fixture_suite_v1","segments":segments,"required_coverage":required,"coverage_owners":owners,
           "accepted_execution_fixture":"tests/fixtures/phase2_execution_native_accepted/native_acceptance.json",
           "accepted_execution_coverage":accepted_execution_coverage,
           "accepted_time_fixture":"tests/fixtures/phase2_time_rule_native_accepted/native_acceptance.json",
           "coverage_contract":"strategy segments plus immutable accepted execution/time fixtures; expected ledgers are never resolver inputs"}
    value=identified(value,"input_fixture_identity")
    value["coverage_plan_identity"]=sha({"required":required,"owners":owners})
    value["per_fixture_identities"]={x["fixture_identifier"]:x["fixture_identity"] for x in segments}
    return value


def coverage_matrix() -> dict:
    fixtures=fixture_suite();suite=strategy_suite()
    value={"schema_version":"nora.phase2_strategy_coverage_matrix_v1","suite_identity":suite["suite_identity"],
           "input_fixture_identity":fixtures["input_fixture_identity"],"required":fixtures["required_coverage"],
           "owners":fixtures["coverage_owners"],"status":"planned_then_rust_verified"}
    return identified(value,"coverage_matrix_identity")


def rng_contract() -> dict:
    return identified({"schema_version":"nora.deterministic_rng_no_draw_v1","seed":0,"draws":0,"purpose":"strategy-suite ordering only"},"rng_identity")


def rust_task_spec() -> dict:
    value={"task_version":1,"task_type":"phase2_ten_strategy_suite_v1","suite":strategy_suite(),
           "fixtures":fixture_suite(),"rng_identity":rng_contract()["rng_identity"]}
    return identified(value,"rust_suite_task_identity")


def run_rust_task() -> dict:
    task=rust_task_spec();wire={k:v for k,v in task.items() if k!="rust_suite_task_identity"}
    binary=ROOT/"engine/target/debug/labengine"
    if not binary.is_file():raise ValueError("build engine/target/debug/labengine first")
    with tempfile.TemporaryDirectory(dir=ROOT) as directory:
        path=Path(directory)/"task.json";path.write_text(json.dumps(wire,separators=(",",":"),sort_keys=True)+"\n")
        result=subprocess.run([str(binary),str(path)],cwd=ROOT,text=True,capture_output=True,check=False)
    if result.returncode or result.stderr.strip():raise ValueError(f"Rust strategy task failed: {result.stderr.strip()}")
    value=json.loads(result.stdout);assert value["ok"] and value["suite_identity"]==strategy_suite()["suite_identity"]
    return value


def rust_evidence(output: dict | None=None) -> dict:
    output=output or run_rust_task();strategies=output["strategy_outputs"]
    ledgers={x["strategy_identifier"]:x["ledger_vector_identity"] for x in strategies}
    no_trade=[x["strategy_identifier"] for x in strategies if x["trades"][0]["trade_ordinal"] is None]
    counts={x["strategy_identifier"]:sum(t["trade_ordinal"] is not None for t in x["trades"]) for x in strategies}
    value={"schema_version":"nora.phase2_ten_strategy_rust_evidence_v1","suite_identity":strategy_suite()["suite_identity"],
           "rust_suite_task_identity":rust_task_spec()["rust_suite_task_identity"],"rust_output":output,
           "evaluated_ast_identities":{x["strategy_identifier"]:x["evaluated_ast_identity"] for x in strategies},
           "intent_identities":{x["strategy_identifier"]:x["intent_identity"] for x in strategies},
           "simulator_output_identities":{x["strategy_identifier"]:x["simulator_output_identity"] for x in strategies},
           "expected_ledger_vector_identities":ledgers,"expected_trade_count_identity":sha(counts),
           "expected_no_trade_identity":sha(no_trade),"expected_trade_counts":counts,"expected_no_trade":no_trade,
           "coverage_classification":"strategy-suite replay evidence contributing to the whole-experiment gate"}
    return identified(value,"combined_rust_evidence_identity")


def experiment_bundle(evidence: dict) -> dict:
    value={"schema_version":"nora.phase2_ten_strategy_linux_experiment_v1","suite":strategy_suite(),
           "fixtures":fixture_suite(),"coverage":coverage_matrix(),"task":rust_task_spec(),"rng":rng_contract(),
           "time_rule_contract_identity":TIME_IDENTITY,"execution_contract_identity":EXECUTION_IDENTITY,
           "indicator_identities":sorted({v for x in strategy_suite()["strategies"] for v in x["indicator_node_identities"].values()}),
           "output_schema_identity":strategy_suite()["ledger_schema"]["strategy_ledger_schema_identity"],
           "expected_rust_evidence_identity":evidence["combined_rust_evidence_identity"]}
    return identified(value,"experiment_bundle_identity")


def replay_record(outputs: list[dict], evidence: dict) -> dict:
    if len(outputs)!=3:raise ValueError("three replay outputs required")
    semantic=[sha(x) for x in outputs];equal=len(set(semantic))==1
    value={"schema_version":"nora.phase2_ten_strategy_replay_record_v1","experiment_bundle_identity":experiment_bundle(evidence)["experiment_bundle_identity"],
           "run_identities":[sha({"run":i+1,"semantic":semantic[i]}) for i in range(3)],"artifact_hashes":semantic,
           "semantic_equal":equal,"destination_inert":equal,"first_divergence":None if equal else "output",
           "classification":"PASS_STRATEGY_SUITE_REPLAY" if equal else "FAIL_DIVERGENCE",
           "gate_scope":"strategy-suite replay evidence contributing to the authoritative whole-experiment gate"}
    return identified(value,"replay_record_identity")
