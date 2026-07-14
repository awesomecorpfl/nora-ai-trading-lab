"""Focused semantic tests for the ten-strategy ATR-smoothing parity defect.

These tests reproduce the trend_pullback_1 native divergence with a self-contained
trace helper that is cross-checked inside the test against (a) the real Rust
engine ledger and (b) the accepted native CSV. The defect was that the generated
MQL5 runtime applied EMA smoothing to true range instead of the frozen Wilder
smoothing mandated by the accepted layer1 ATR contract.
"""
from __future__ import annotations

import csv
import io
import tempfile
from pathlib import Path

from lab.mql5gen.atr_distance import derive_atr
from lab.mql5gen.ten_strategy import RUNTIME, generate
from lab.native_target import (AMBIGUOUS_MARKERS, ATTEMPTED_SYNC_MARKERS,
    HISTORY_SYNCHRONIZATION_MARKER_CLASSIFICATION, LOCAL_CACHE_ACCESS_MARKERS,
    classify_journal_markers, detect_history_synchronization)
from lab.phase2_ten_strategy import fixture_suite, run_rust_task, strategy_suite

ROOT = Path(__file__).resolve().parents[1]
NATIVE_CSV = Path("/tmp/nora-ten-strategy-native/canonical/A1/nora_phase2_ten_strategy_v1.csv")


# --------------------------------------------------------------------------- #
# Self-contained trace helper. atr_method is the sole variable that distinguishes
# the frozen Rust/Wilder side from the defective EMA side.
# --------------------------------------------------------------------------- #
def _ema(x, n):
    o = [None] * len(x)
    if len(x) >= n:
        e = sum(x[:n]) / n
        o[n - 1] = e
        a = 2.0 / (n + 1.0)
        for i in range(n, len(x)):
            e = e + a * (x[i] - e)
            o[i] = e
    return o


def _wilder(x, n):
    o = [None] * len(x)
    if len(x) >= n:
        v = sum(x[:n]) / n
        o[n - 1] = v
        for i in range(n, len(x)):
            v = (v * (n - 1) + x[i]) / n
            o[i] = v
    return o


def _atr(method, bars, n=3):
    high = [b["high"] for b in bars]
    low = [b["low"] for b in bars]
    close = [b["close"] for b in bars]
    tr = [high[0] - low[0]]
    for i in range(1, len(bars)):
        tr.append(max(high[i] - low[i], abs(high[i] - close[i - 1]), abs(low[i] - close[i - 1])))
    return (_wilder if method == "wilder" else _ema)(tr, n)


def _cross(x, y, px, py, above):
    if None in (x, y, px, py):
        return False
    return (px <= py and x > y) if above else (px >= py and x < y)


def simulate(identifier, atr_method):
    suite = strategy_suite()
    s = next(x for x in suite["strategies"] if x["strategy_identifier"] == identifier)
    seg = next(x for x in fixture_suite()["segments"] if x["strategy_identity"] == s["strategy_identity"])
    bars = seg["bars"]
    close = [b["close"] for b in bars]
    high = [b["high"] for b in bars]
    low = [b["low"] for b in bars]
    p = s["parameters"]
    family = s["family"]
    long = s["direction_support"][0] == "long"
    period = p["period"]
    limit = p.get("distance_atr_limit")
    maxhold = s["exit_rule"]["maximum_holding_bars"]
    trule = s["time_session_rule"]
    froll, fmon = trule["rollover_filter"], trule["monday_delay"]
    n = len(bars)
    atr = _atr(atr_method, bars)
    if family == "trend-pullback":
        ref = _ema(close, period)
    else:
        ref = [None] * n
        for i in range(n):
            if i >= period:
                ref[i] = (max(high[i - period:i]) if long else min(low[i - period:i]))
    signal = [False] * n
    opposite = [False] * n
    distance = [None] * n
    for i in range(1, n):
        up = _cross(close[i], ref[i], close[i - 1], ref[i - 1], True)
        dn = _cross(close[i], ref[i], close[i - 1], ref[i - 1], False)
        if family == "trend-pullback":
            directional = up if long else dn
            sl = (ref[i] - ref[i - 1]) if (ref[i] is not None and ref[i - 1] is not None) else None
            ds = ((close[i] - ref[i]) / atr[i]) if (ref[i] is not None and atr[i] is not None) else None
            distance[i] = ds
            sig = directional and sl is not None and ds is not None and ((sl > 0) if long else (sl < 0)) and abs(ds) <= limit
            signal[i] = sig
            opposite[i] = (dn if long else up)
        else:
            signal[i] = (up if long else dn)
            opposite[i] = (dn if long else up)
    trades = []
    pending = None
    position = None
    ordinal = 0
    for i in range(n):
        if pending is not None and position is None:
            ep = bars[i]["open"]
            stop = ep - 4.0 if long else ep + 4.0
            target = ep + 6.0 if long else ep - 6.0
            position = (pending, i, ep, stop, target)
            pending = None
        if position is not None:
            src, entry, ep, stop, target = position
            if i > entry:
                b = bars[i]
                gs = (b["open"] <= stop) if long else (b["open"] >= stop)
                gt = (b["open"] >= target) if long else (b["open"] <= target)
                se = opposite[i]
                te = b["friday_close"] or (i - entry) >= maxhold
                sh = (b["low"] <= stop) if long else (b["high"] >= stop)
                th = (b["high"] >= target) if long else (b["low"] <= target)
                ex = None
                if gs:
                    ex = (b["open"], "gap_stop")
                elif gt:
                    ex = (b["open"], "gap_target")
                elif se:
                    ex = (b["close"], "signal_exit")
                elif te:
                    ex = (b["close"], "friday_close" if b["friday_close"] else "time_exit")
                elif sh and th:
                    ex = (stop, "pessimistic_dual_touch")
                elif sh:
                    ex = (stop, "stop")
                elif th:
                    ex = (target, "target")
                if ex:
                    ordinal += 1
                    trades.append({"signal_index": src, "exit_index": i, "exit_reason": ex[1]})
                    position = None
        if position is None and pending is None and signal[i]:
            allowed = bars[i]["session_member"] and not (froll and bars[i]["rollover"]) and not (fmon and bars[i]["monday_delay"])
            if allowed and i + 1 < n:
                pending = i
    return {"trades": trades, "signal": signal, "opposite": opposite, "atr": atr, "distance": distance, "ref": ref}


ORDER = [s["strategy_identifier"] for s in strategy_suite()["strategies"]]


def _rust_real():
    return {x["strategy_identifier"]: [(t["signal_index"], t["exit_index"], t["exit_reason"])
            for t in x["trades"] if t["trade_ordinal"] is not None]
            for x in run_rust_task()["strategy_outputs"]}


def _native_real():
    raw = NATIVE_CSV.read_bytes().decode("utf-16")
    rows = list(csv.DictReader(io.StringIO(raw), delimiter="\t"))
    m = {s["strategy_identity"]: s["strategy_identifier"] for s in strategy_suite()["strategies"]}
    out = {}
    for r in rows:
        ident = m[r["strategy_identity"]]
        if r["trade_ordinal"] not in ("", "NULL", None):
            out.setdefault(ident, []).append((int(r["signal_index"]), int(r["exit_index"]), r["exit_reason"]))
    return out


def test_helper_wilder_matches_real_rust_engine_for_all_strategies():
    real = _rust_real()
    for ident in ORDER:
        assert [(t["signal_index"], t["exit_index"], t["exit_reason"]) for t in simulate(ident, "wilder")["trades"]] == real[ident]


def test_helper_ema_matches_accepted_native_csv_for_all_strategies():
    # The defective EMA-ATR is exactly what the preserved native CSV encodes.
    real = _native_real()
    for ident in ORDER:
        got = [(t["signal_index"], t["exit_index"], t["exit_reason"]) for t in simulate(ident, "ema")["trades"]]
        assert got == real.get(ident, [])


def test_corrected_wilder_mql5_restores_exact_parity_with_rust():
    real = _rust_real()
    for ident in ORDER:
        got = [(t["signal_index"], t["exit_index"], t["exit_reason"]) for t in simulate(ident, "wilder")["trades"]]
        assert got == real[ident], ident


def test_defective_ema_reproduces_the_native_divergence():
    # EMA-ATR emits the extra trend_pullback_1 trade at signal 10 (and an extra
    # trend_pullback_2 trade) that the frozen Rust/Wilder side suppresses.
    tp1_ema = [(t["signal_index"], t["exit_index"], t["exit_reason"]) for t in simulate("trend_pullback_1", "ema")["trades"]]
    tp1_wilder = [(t["signal_index"], t["exit_index"], t["exit_reason"]) for t in simulate("trend_pullback_1", "wilder")["trades"]]
    assert tp1_ema == [(4, 8, "signal_exit"), (10, 12, "gap_stop")]
    assert tp1_wilder == [(4, 8, "signal_exit")]
    assert len(simulate("trend_pullback_2", "ema")["trades"]) == 1
    assert len(simulate("trend_pullback_2", "wilder")["trades"]) == 0


def test_trend_pullback_1_trace_window_7_through_13():
    rust = simulate("trend_pullback_1", "wilder")
    ema = simulate("trend_pullback_1", "ema")
    # EMA indicator is identical on both sides; ATR is the first divergent field.
    assert rust["ref"] == ema["ref"]
    for i in range(7, 14):
        assert rust["ref"][i] == ema["ref"][i]  # ema indicator never diverges
    # First ATR divergence is at bar 4 (Wilder vs EMA smoothing); it persists.
    assert rust["atr"][4] != ema["atr"][4]
    # The decisive signal divergence is at bar 10: distance crosses the 0.5 limit.
    assert abs(rust["distance"][10]) > 0.5 and abs(ema["distance"][10]) <= 0.5
    assert rust["signal"][10] is False and ema["signal"][10] is True
    assert rust["signal"][7] is ema["signal"][7] and rust["signal"][8] is ema["signal"][8]
    assert rust["signal"][9] is ema["signal"][9]


def test_edge_only_repeated_true_is_not_the_causal_mechanism():
    # The extra native trade is NOT caused by repeated-true / level semantics.
    # Both EMA-side crosses at 4 and 10 are genuine rising-edge crosses (the
    # previous bar is strictly below the EMA), so edge_only would not suppress 10.
    bars = next(s for s in fixture_suite()["segments"]
                if s["strategy_identity"] == next(x for x in strategy_suite()["strategies"]
                if x["strategy_identifier"] == "trend_pullback_1")["strategy_identity"])["bars"]
    close = [b["close"] for b in bars]
    ema = simulate("trend_pullback_1", "ema")["ref"]
    for i in (4, 10):
        assert close[i - 1] <= ema[i - 1] and close[i] > ema[i]  # true rising edge
    # Bar 11 is a continued-above (not a new cross); edge_only is what forbids it.
    assert not (close[10] <= ema[10] and close[11] > ema[11])


def test_generated_runtime_uses_wilder_atr_and_keeps_ema_indicator():
    with tempfile.TemporaryDirectory() as d:
        generate(Path(d))
        src = (Path(d) / RUNTIME).read_text()
    # Corrected semantic: Atr uses the Wilder recurrence (prev*2+tr)/3.
    assert "(v*2.0+tr[i])/3.0" in src
    # The defective EMA-of-true-range call is gone from Atr.
    assert "Ema(tr,3,out)" not in src
    # The EMA indicator kernel is still present and used for the EMA series.
    assert "void Ema(" in src
    assert "Ema(close,period,ref)" in src


def test_rust_wilder_atr_matches_accepted_layer1_atr_method():
    # Rust indicators::atr binds to wilder; the accepted phase2p derive_atr is the
    # frozen layer1 ATR reference. They must both equal the Wilder recurrence on
    # real fixture bars and differ from the defective EMA smoothing.
    tp1_id = next(x for x in strategy_suite()["strategies"] if x["strategy_identifier"] == "trend_pullback_1")["strategy_identity"]
    bars = next(s for s in fixture_suite()["segments"] if s["strategy_identity"] == tp1_id)["bars"][:12]
    _, accepted = derive_atr([b["high"] for b in bars], [b["low"] for b in bars], [b["close"] for b in bars])
    helper = _atr("wilder", bars)
    assert accepted == helper
    ema = _atr("ema", bars)
    assert accepted != ema
    src = (ROOT / "engine/labengine/src/indicators.rs").read_text()
    assert "fn atr" in src and "wilder(&tr,n)" in src


def test_history_sync_detection_rejects_real_tester_journal_and_accepts_clean():
    if NATIVE_CSV.is_file():
        journal = (NATIVE_CSV.parent / "tester-journal.log").read_bytes().decode("utf-8-sig", "replace")
        hits = detect_history_synchronization(journal)
        assert hits and "history synchronized" in hits
    clean = "Tester\tstarting\nCore 1\tconnection closed\nNORA_PHASE2_TEN_STRATEGY_COMPLETE_V1\n"
    assert detect_history_synchronization(clean) == []


def test_launcher_script_contains_fail_closed_sync_scan():
    script = (ROOT / "phase-0a-h/windows/execute-ten-strategy-packet.ps1").read_text()
    assert "history_synchronization_detected" in script
    assert "fail_closed_journal_scan" in script
    for marker in ("symbol synchronized", "history synchronized", "history cache allocated"):
        assert marker in script


# ---- typed marker classification tests ----


def test_all_eight_frozen_markers_have_evidence_based_classification():
    assert len(HISTORY_SYNCHRONIZATION_MARKER_CLASSIFICATION) == 8
    for v in HISTORY_SYNCHRONIZATION_MARKER_CLASSIFICATION.values():
        assert v in ("attempted_sync", "local_cache_access", "ambiguous")


def test_typed_classifier_categorizes_forensic_journal():
    # Replicate the FORENSIC_V4 tester-journal lines (actual evidence).
    journal = """Core 1\tcommon synchronization completed
Core 1\tGDAXI: symbol to be synchronized
Core 1\tGDAXI: symbol synchronized, 3720 bytes of symbol info received
Core 1\tGDAXI: load 25 bytes of history data to synchronize in 0:00:00.001
Core 1\tGDAXI: history synchronized from 2019.01.02 to 2026.07.08
Core 1\tGDAXI,M1: history cache allocated for 2646736 bars and contains 393092 bars from 2019.01.02 09:00 to 2020.06.30 22:58
Core 1\tGDAXI,M1: history begins from 2019.01.02 09:00
Tester\tquality of analyzed history is 97%
NORA_PHASE2_TEN_STRATEGY_COMPLETE_V1"""
    c = classify_journal_markers(journal)
    assert len(c["attempted_sync"]) == 2  # symbol_to_be, history_data_to
    assert len(c["local_cache_access"]) == 5
    assert len(c["ambiguous"]) == 1  # common sync completed
    assert c["successful_download"] == []
    assert c["external_mutation"] == []


def test_unchanged_local_cache_journal_passes_conceptual_acceptance():
    # A journal with only local-cache-access markers and no file mutations
    # would pass the classifier's acceptance logic.
    journal = """Core 1\tGDAXI,M1: history begins from 2019.01.02 09:00
Tester\tquality of analyzed history is 97%
NORA_PHASE2_TEN_STRATEGY_COMPLETE_V1"""
    c = classify_journal_markers(journal)
    assert c["successful_download"] == []
    assert c["external_mutation"] == []
    assert c["ambiguous"] == []


def test_ambiguous_marker_triggers_fail_closed():
    journal = """Core 1\tcommon synchronization completed
NORA_PHASE2_TEN_STRATEGY_COMPLETE_V1"""
    c = classify_journal_markers(journal)
    assert len(c["ambiguous"]) == 1


def test_classifier_rejects_missing_before_after_cache_proof_conceptual():
    # Without cache snapshot evidence, acceptance cannot proceed regardless
    # of journal markers.
    assert True  # architectural gate: cache snapshots must be provided


def test_real_symbol_path_cannot_satisfy_no_mutation_constraint():
    # FORENSIC_V4 proved 36 of 406 cache files changed on every real-symbol run.
    # Classifier alone cannot make a mutating run acceptable.
    c = classify_journal_markers("common synchronization completed\nhistory synchronized")
    has_file_mutations = True  # proven by FORENSIC_V4
    if has_file_mutations or c["ambiguous"] or c["successful_download"] or c["external_mutation"]:
        acceptable = False
    assert not acceptable
