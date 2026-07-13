"""Canonical, parameterized Phase-2 time-rule contracts."""
from __future__ import annotations
import hashlib, json

VERSION = "nora.phase2.time_rules_contracts_v1"

def canon(v): return json.dumps(v, sort_keys=True, separators=(",", ":"))
def identity(v): return hashlib.sha256(canon(v).encode()).hexdigest()

def contracts():
    dataset = {"schema_version":"nora.dataset_clock_v1","timezone_identity":"america_new_york_plus_7_v1","dst_regime_identity":"new_york_dst_v1","timestamp_unit":"epoch_seconds","timestamp_interpretation":"instant","bar_timestamp_semantics":"start","conversion_state":"declared_not_converted","conversion_history_identity":identity([]),"derived_timeframe_anchoring_contract":"strategy_clock_session_boundary_v1"}
    strategy = {"schema_version":"nora.strategy_clock_v1","clock":"america_new_york_plus_7_v1","evaluates":["entry_session","exit_session","friday_close","rollover","monday_open","orb","daily_reset"]}
    session = {"schema_version":"nora.session_clock_v1","clock":"america_new_york_plus_7_v1","start":"09:30","end":"16:00","start_inclusive":True,"end_exclusive":True,"crosses_midnight":False,"weekdays":["Mon","Tue","Wed","Thu","Fri"],"holiday_behavior":"unsupported"}
    anchoring = {"schema_version":"nora.derived_timeframe_anchor_v1","clock":"america_new_york_plus_7_v1","session_boundary":"17:00","timeframes":["M5","H1"],"epoch_ordering":"strict","fall_fold":"distinct_epoch_anchors"}
    reasons = {"schema_version":"nora.time_rule_reason_codes_v1","codes":["conversion_rejected","friday_close","rollover","monday_delay","orb_active","session_member","outside_session","ok"]}
    for value, key in ((dataset,"dataset_clock_identity"),(strategy,"strategy_clock_identity"),(session,"session_clock_identity"),(anchoring,"anchoring_identity"),(reasons,"reason_code_identity")):
        value[key] = identity(value)
    return {"schema_version":VERSION,"dataset":dataset,"strategy":strategy,"session":session,"dst_regime":{"schema_version":"nora.dst_regime_v1","identity":"new_york_dst_v1","base":"America/New_York","broker_adjustment_seconds":25200},"anchoring":anchoring,"reasons":reasons}
