"""Frozen ten-strategy Phase-2 parity suite and deterministic fixture contracts."""
from __future__ import annotations

import copy
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
        closes = ([base,base-1,base-2,base-1,base+1,base+3,base+2,base+4,base+1,base+2,base+5,base+4]
                  if side == "long" else [base,base+1,base+2,base+1,base-1,base-3,base-2,base-4,base-1,base-2,base-5,base-4])
        bars=[]
        for row, close in enumerate(closes):
            open_=close + (-0.5 if side == "long" else 0.5)
            span=2.0 if row in (6,8) else 1.0
            bars.append({"timestamp":f"2040-01-{index+1:02d} {row:02d}:00","open":open_,"high":max(open_,close)+span,"low":min(open_,close)-span,"close":close,
                         "session_member": row not in (0,9), "friday_close": row==10 and index in (2,7), "rollover":row==4 and strategy["time_session_rule"]["rollover_filter"],
                         "monday_delay":row==4 and strategy["time_session_rule"]["monday_delay"]})
        segment={"fixture_identifier":f"fixture_{strategy['strategy_identifier']}","strategy_identity":strategy["strategy_identity"],"bars":bars,
                 "coverage_tags":["long_entry" if side=="long" else "short_entry","null_warmup_suppression","next_open_entry","session_filtering","terminal_source_not_executed","no_overlap"]}
        segments.append(identified(segment,"fixture_identity"))
    required=["long_entry","short_entry","no_trade_result","repeated_true_signals","null_warmup_suppression","next_open_entry","gap_entry","signal_exit","time_exit","friday_close_exit","stop_exit","target_exit","pessimistic_dual_touch","terminal_source_not_executed","session_filtering","rollover_filtering","monday_delay_filtering","completed_level_shift","multiple_sequential_trades","no_overlap"]
    # Coverage ownership is frozen here and verified against Rust outcomes later.
    owners={name:[segments[i % 10]["fixture_identifier"]] for i,name in enumerate(required)}
    value={"schema_version":"nora.phase2_ten_strategy_fixture_suite_v1","segments":segments,"required_coverage":required,"coverage_owners":owners}
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
