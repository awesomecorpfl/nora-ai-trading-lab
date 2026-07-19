"""Local execution-strategy generation and one-entry/one-exit reconciliation."""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from lab.phase2_execution import canon, sha

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "engine" / "target" / "debug" / "labengine"
SCHEMA = "nora.phase2.local_execution_strategy_case_v1"

CASE = {
    "schema_version": SCHEMA,
    "case_id": "one_long_entry_one_signal_exit",
    "side": "long",
    "bars": [
        {"timestamp": "2041.01.01 00:00", "open": 10.0, "high": 10.5, "low": 9.5, "close": 10.0},
        {"timestamp": "2041.01.01 00:01", "open": 11.0, "high": 11.5, "low": 10.5, "close": 11.0},
        {"timestamp": "2041.01.01 00:02", "open": 12.0, "high": 12.5, "low": 11.5, "close": 12.5},
    ],
    "entry_signal": [True, False, False],
    "exit_signal": [False, False, True],
    "bracket": {"stop_offset": 2.0, "target_offset": 3.0},
    "execution_model": "ohlc_unambiguous_v1",
    "entry_timing": "next_open",
    "position_policy": "one_at_a_time",
}


def generate_execution_strategy() -> dict[str, Any]:
    value = dict(CASE)
    value["case_identity"] = sha(CASE)
    value["generated_task_identity"] = sha({"case_identity": value["case_identity"], "task_type": "simulate_market_v1", "contract": "local_one_entry_one_exit_v1"})
    return value


def _write_inputs(root: Path) -> dict[str, str]:
    ts = [bar["timestamp"] for bar in CASE["bars"]]
    pq.write_table(pa.table({
        "timestamp": ts,
        "open": pa.array([bar["open"] for bar in CASE["bars"]], type=pa.float64()),
        "high": pa.array([bar["high"] for bar in CASE["bars"]], type=pa.float64()),
        "low": pa.array([bar["low"] for bar in CASE["bars"]], type=pa.float64()),
        "close": pa.array([bar["close"] for bar in CASE["bars"]], type=pa.float64()),
    }), root / "market.parquet")
    pq.write_table(pa.table({"timestamp": ts, "entry_intent": pa.array(CASE["entry_signal"], type=pa.bool_())}), root / "entry.parquet")
    pq.write_table(pa.table({"timestamp": ts, "exit_intent": pa.array(CASE["exit_signal"], type=pa.bool_())}), root / "exit.parquet")
    return {"market": str(root / "market.parquet"), "entry": str(root / "entry.parquet"), "exit": str(root / "exit.parquet"), "trades": str(root / "trades.parquet")}


def run_execution_strategy() -> dict[str, Any]:
    if not ENGINE.is_file():
        raise ValueError("build engine/target/debug/labengine first")
    generated = generate_execution_strategy()
    with tempfile.TemporaryDirectory(dir=ROOT) as directory:
        root = Path(directory)
        paths = _write_inputs(root)
        task = {
            "task_version": 1,
            "task_type": "simulate_market_v1",
            "market_path": paths["market"],
            "entry_intent_path": paths["entry"],
            "exit_intent_path": paths["exit"],
            "output_path": paths["trades"],
            "config": {
                "schema_version": 1,
                "side": "long",
                "price_column": "open",
                "entry_column": "entry_intent",
                "exit_column": "exit_intent",
                "position_policy": "one_at_a_time",
                "terminal_policy": "leave_open",
                "initial_bracket": {
                    "model": "fixed_price_offsets_v1",
                    "stop_offset": 2.0,
                    "target_offset": 3.0,
                    "output_path": str(root / "brackets.parquet"),
                },
                "initial_bracket_execution": {
                    "model": "ohlc_unambiguous_v1",
                    "event_output_path": str(root / "events.parquet"),
                },
            },
        }
        task_path = root / "strategy.task.json"
        task_path.write_text(canon(task) + "\n")
        result = subprocess.run([str(ENGINE), str(task_path)], cwd=ROOT, capture_output=True, text=True)
        if result.returncode or result.stderr.strip():
            raise ValueError(f"local execution strategy failed: {result.stderr.strip() or result.stdout.strip()}")
        summary = json.loads(result.stdout)
        rows = pq.read_table(paths["trades"]).to_pylist()
        events = pq.read_table(root / "events.parquet").to_pylist()

    actual_rows = []
    for row in rows:
        actual = {key: row[key] for key in ("side", "entry_index", "entry_price", "exit_index", "exit_price", "bars_held", "gross_pnl_per_unit")}
        actual["exit_reason"] = "signal" if summary["signal_closes"] else (events[0]["exit_reason"] if events else None)
        actual_rows.append(actual)
    expected_rows = [{"side": "long", "entry_index": 0, "entry_price": 10.0, "exit_index": 2, "exit_price": 12.0, "bars_held": 2, "gross_pnl_per_unit": 2.0, "exit_reason": "signal"}]
    reconciliation = {
        "expected_trade_count": len(expected_rows),
        "actual_trade_count": len(actual_rows),
        "expected_rows": expected_rows,
        "actual_rows": actual_rows,
        "expected_exit_reason": "signal",
        "actual_exit_reason": actual_rows[0]["exit_reason"] if actual_rows else None,
    }
    reconciliation["status"] = "PASS" if reconciliation["expected_rows"] == reconciliation["actual_rows"] else "FAIL"
    reconciliation["reconciliation_identity"] = sha({key: value for key, value in reconciliation.items() if key != "reconciliation_identity"})
    body = {
        "schema_version": "nora.phase2.local_execution_strategy_reconciliation_v1",
        "strategy": generated,
        "simulator_contract": "simulate_market_v1",
        "simulator_identity": summary["simulator_semantic_identity"],
        "reconciliation": reconciliation,
        "classification": "PASS_LOCAL_EXECUTION_STRATEGY_RECONCILIATION" if reconciliation["status"] == "PASS" else "FAIL_LOCAL_EXECUTION_STRATEGY_RECONCILIATION",
    }
    body["result_identity"] = sha(body)
    return body


def verify_execution_strategy(value: dict[str, Any]) -> bool:
    if not isinstance(value, dict) or value.get("result_identity") != sha({key: item for key, item in value.items() if key != "result_identity"}):
        raise ValueError("local execution strategy identity mismatch")
    if value.get("classification") != "PASS_LOCAL_EXECUTION_STRATEGY_RECONCILIATION":
        raise ValueError("local execution strategy reconciliation is not a pass")
    if value["reconciliation"]["expected_rows"] != value["reconciliation"]["actual_rows"]:
        raise ValueError("local execution strategy ledger mismatch")
    return True
