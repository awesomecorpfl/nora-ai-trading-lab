"""Authoritative Phase-2 Layer-1 inventory and initial-v1 dependency records."""
from __future__ import annotations

from lab.phase2_execution import sha

PRIMITIVES = {
 "sma": ("SMA", ["value"], "ACCEPTED", "period-1; null window propagates", []),
 "ema": ("EMA", ["value"], "ACCEPTED", "arithmetic seed at period-1; null resets seed", []),
 "adx": ("ADX", ["adx"], "IMPLEMENTED_UNPROVED", "Wilder DX then Wilder ADX; zero denominator unavailable", ["ATR-style true range"]),
 "er": ("ER", ["ratio"], "IMPLEMENTED_UNPROVED", "period warmup; flat volatility returns zero", []),
 "kama": ("KAMA", ["value"], "IMPLEMENTED_UNPROVED", "period warmup; ER-driven seed and recurrence", ["ER"]),
 "macd": ("MACD", ["macd","signal","histogram"], "ACCEPTED", "slow-1 MACD warmup; compact signal realigned; null until available", ["EMA"]),
 "linear_regression": ("LinearRegression", ["value","slope"], "IMPLEMENTED_UNPROVED", "period-1 warmup", []),
 "rsi": ("RSI", ["value"], "IMPLEMENTED_UNPROVED", "period warmup; flat=50; loss-zero gain-positive=100", []),
 "cci": ("CCI", ["value"], "IMPLEMENTED_UNPROVED", "period-1 warmup; zero deviation returns zero", []),
 "roc": ("ROC", ["value"], "IMPLEMENTED_UNPROVED", "period warmup; zero denominator unavailable", []),
 "stochastic": ("Stochastic", ["k","d"], "IMPLEMENTED_UNPROVED", "K warmup period-1; D requires complete K window; zero range=50", ["Highest","Lowest","SMA"]),
 "atr": ("ATR", ["value"], "ACCEPTED", "period-1 Wilder warmup; null input unavailable", []),
 "bollinger": ("BollingerBands", ["middle","upper","lower","width"], "IMPLEMENTED_UNPROVED", "period-1 warmup; population deviation; zero middle width=0", ["SMA"]),
 "keltner": ("Keltner", ["middle","upper","lower"], "IMPLEMENTED_UNPROVED", "aligned EMA and ATR availability", ["EMA","ATR"]),
 "highest": ("Highest", ["value"], "ACCEPTED", "period-1 warmup; any null window unavailable", []),
 "lowest": ("Lowest", ["value"], "ACCEPTED", "period-1 warmup; any null window unavailable", []),
 "session_ohlc": ("SessionOHLC", ["open","high","low","close"], "IMPLEMENTED_UNPROVED", "available from first declared session row; reset at declared trading day", ["time rules"]),
 "vwap": ("VWAP", ["value"], "IMPLEMENTED_UNPROVED", "available from first declared session row; reset daily; volume required; zero volume=0", ["Session clock","volume"]),
}
TRANSFORMS = {
 "cross": ("Cross", ["boolean"], "ACCEPTED", "row 0 unavailable; any current/previous null unavailable", []),
 "slope": ("Slope", ["value"], "ACCEPTED", "lookback warmup; either endpoint null unavailable", []),
 "distance_atr": ("DistanceAtr", ["value"], "ACCEPTED", "any input null or non-positive ATR unavailable", ["ATR"]),
 "percentile": ("Percentile", ["rank"], "ACCEPTED", "complete lookback required; average-rank ties", []),
}
SELECTED = ("layer1.ema", "layer1.highest", "layer1.lowest")


def _entry(prefix, key, spec):
    name, outputs, status, nulls, deps = spec; selected=f"{prefix}.{key}" in SELECTED
    accepted=status=="ACCEPTED"; typed = key in ("atr","distance_atr") or selected
    mql = accepted or selected
    identity=sha({"schema":"nora.layer1_node_v1","id":f"{prefix}.{key}","outputs":outputs,"null_semantics":nulls})
    native_result = "accepted_narrow" if accepted else "not_attempted"
    gap = ("complete Phase-2 gate; preserve narrow accepted evidence" if accepted
           else "genuine native compilation, returned results, empirical budget proposal, and explicit acceptance" if selected
           else "typed AST/MQL5/native evidence not required before the first ten strategies")
    return {"canonical_id":f"{prefix}.{key}","canonical_identity":identity,"name":name,
            "classification":status,"rust":{"status":"implemented","binding":"engine/labengine/src/indicators.rs"},
            "typed_ast":{"status":"implemented_nonsearchable" if typed else "absent","schema_version":1 if typed else None},
            "outputs":{"arity":len(outputs),"names":outputs},"null_warmup_semantics":nulls,
            "mql5_translation":{"status":"generated" if mql else "absent","mode":"independent_generated" if selected else "preserved" if accepted else None},
            "local_fixture":{"status":"fixed" if selected or accepted else "engine_unit_only"},
            "native_compiler_evidence":"accepted" if accepted else "pending" if selected else "absent",
            "native_result":native_result,"native_reconciliation":"accepted" if accepted else "pending" if selected else "absent",
            "grammar_admission":"admitted_narrow" if key in ("atr","distance_atr") else "not_admitted",
            "searchable":False,"dependencies":deps,"first_batch":selected,"remaining_gap":gap}


def matrix():
    nodes=[_entry("layer1",k,v) for k,v in PRIMITIVES.items()]+[_entry("transform",k,v) for k,v in TRANSFORMS.items()]
    value={"schema_version":"nora.layer1_authoritative_matrix_v1","phase":2,"search_authorized":False,
           "phase2_complete":False,"nodes":nodes}
    value["counts"]={s:sum(x["classification"]==s for x in nodes) for s in
                     ("ACCEPTED","IMPLEMENTED_UNPROVED","PARTIALLY_PROVEN","ABSENT","DEFERRED","NOT_REQUIRED_FOR_INITIAL_V1_GRAMMAR")}
    value["matrix_identity"]=sha(value);return value


def dependency_map():
    trend_common=["layer1.ema","transform.slope","layer1.atr","transform.distance_atr","transform.cross"]
    breakout_common=["layer1.highest","layer1.lowest","transform.cross"]
    strategies=[]
    for i,(side,period,pullback) in enumerate((("long",3,.5),("short",3,.5),("long",5,1.0),("short",5,1.0),("long",5,.25)),1):
        strategies.append({"id":f"trend_pullback_{i}","family":"trend-pullback","side":side,"ema_period":period,
                           "distance_atr_limit":pullback,"nodes":trend_common,"entry_timing":"next_open"})
    for i,(side,period) in enumerate((("long",3),("short",3),("long",5),("short",5),("long",8)),1):
        strategies.append({"id":f"close_breakout_{i}","family":"close-confirmed breakout","side":side,"period":period,
                           "completed_level_shift":1,"nodes":breakout_common,"entry_timing":"next_open"})
    value={"schema_version":"nora.initial_v1_dependency_map_v1","strategy_count":10,"strategies":strategies,
           "mandatory_nodes":["layer1.ema","layer1.highest","layer1.lowest","layer1.atr","transform.distance_atr","transform.slope","transform.cross"],
           "optional_diversity_nodes":["layer1.rsi","layer1.roc","layer1.bollinger","layer1.keltner"],
           "already_accepted":["layer1.atr","transform.distance_atr","transform.slope","transform.cross"],
           "blocking_nodes":[],"accepted_batch_nodes":list(SELECTED),"not_needed_before_first_ten":[f"layer1.{x}" for x in ("adx","er","kama","linear_regression","rsi","cci","roc","stochastic","bollinger","keltner","session_ohlc","vwap")],
           "multi_output_dependencies":[],"session_time_dependencies":["accepted time-rule 18-scenario contract"],
           "execution_dependencies":["accepted execution-model 12-scenario next-open contract"]}
    value["dependency_map_identity"]=sha(value);return value


def batch_plan(node_identities: dict):
    value={"schema_version":"nora.layer1_first_batch_plan_v1","selected_nodes":list(SELECTED),
           "selected_node_identities":node_identities,"reference_modes":{x:{"mode":"independent_generated","native_mt5_indicator":False,"applied_price":None,"buffer":None,"shift":0,"indexing":"oldest_to_newest_embedded_rows"} for x in SELECTED},
           "reason":"smallest dependency-complete unaccepted batch for five trend-pullback and five close-confirmed breakout designs",
           "excluded":{"accepted":"SMA, MACD, ATR, Cross, Slope, DistanceAtr, Percentile",
                       "complex_or_optional":"ADX, ER, KAMA, LinearRegression, RSI, CCI, ROC, Stochastic, Bollinger, Keltner",
                       "not_required":"SessionOHLC, VWAP"},"grammar_admitted":False,"searchable":False}
    value["batch_plan_identity"]=sha(value);return value
