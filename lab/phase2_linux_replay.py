"""One complete deterministic Linux experiment replay for the Phase-2 gate."""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from lab.phase2_execution import sha

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "engine" / "target" / "debug" / "labengine"
SOURCE = ROOT / "tests" / "fixtures" / "phase2_linux_replay_m1.parquet"
SCHEMA = "nora.phase2_linux_experiment_replay_v1"


def _run_task(work: Path, name: str, spec: dict[str, Any]) -> dict[str, Any]:
    task_path = work / f"{name}.task.json"
    task_path.write_text(json.dumps(spec, sort_keys=True, separators=(",", ":")) + "\n")
    result = subprocess.run([str(ENGINE), str(task_path)], cwd=ROOT, capture_output=True, text=True)
    if result.returncode or result.stderr.strip():
        raise ValueError(f"Linux replay task {name} failed: {result.stderr.strip() or result.stdout.strip()}")
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Linux replay task {name} returned malformed JSON") from exc
    if not value.get("ok"):
        raise ValueError(f"Linux replay task {name} returned failure: {value}")
    return value


def _ast(op: str, threshold: float) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "root": {
            "kind": "compare",
            "op": op,
            "left": {"kind": "numeric_series", "ref": {"series": "sma1", "type": "numeric"}},
            "right": {"kind": "number", "value": threshold},
        },
    }


def _body() -> dict[str, Any]:
    if not ENGINE.is_file():
        raise ValueError("build engine/target/debug/labengine first")
    if not SOURCE.is_file():
        raise ValueError(f"missing replay source fixture: {SOURCE}")
    with tempfile.TemporaryDirectory(dir=ROOT) as directory:
        work = Path(directory)
        aggregated = work / "aggregated.parquet"
        indicators = work / "indicators.parquet"
        entry_ast = work / "entry_ast.parquet"
        exit_ast = work / "exit_ast.parquet"
        entry_intents = work / "entry_intents.parquet"
        exit_intents = work / "exit_intents.parquet"
        trades = work / "trades.parquet"
        metrics = work / "metrics.json"

        ingestion = _run_task(work, "ingestion", {
            "task_version": 1, "task_type": "validate_dataset", "input_path": str(SOURCE),
            "expected_contract_version": 1,
        })
        aggregation = _run_task(work, "aggregation", {
            "task_version": 1, "task_type": "aggregate_m1", "input_path": str(SOURCE),
            "target_timeframe": "M5", "output_path": str(aggregated),
            "completeness_policy": "omit_edge_partials_v1",
        })
        indicator = _run_task(work, "indicators", {
            "task_version": 1, "task_type": "compute_indicators", "input_path": str(SOURCE),
            "output_path": str(indicators), "indicators": [{"name": "SMA", "output": "sma1", "period": 1}],
        })
        entry_eval = _run_task(work, "entry_ast", {
            "task_version": 1, "task_type": "evaluate_ast", "input_path": str(indicators),
            "output_path": str(entry_ast), "output": "entry_signal", "ast": _ast("gt", 1.1005),
        })
        exit_eval = _run_task(work, "exit_ast", {
            "task_version": 1, "task_type": "evaluate_ast", "input_path": str(indicators),
            "output_path": str(exit_ast), "output": "exit_signal", "ast": _ast("gt", 1.1028),
        })
        entry = _run_task(work, "entry_intents", {
            "task_version": 1, "task_type": "build_entry_intents", "input_path": str(entry_ast),
            "output_path": str(entry_intents), "output": "entry_intent",
            "condition": {"schema_version": 1, "side": "long", "entry": {"signal": {"series": "entry_signal", "type": "boolean"}, "timing": "next_open"}},
        })
        exit_ = _run_task(work, "exit_intents", {
            "task_version": 1, "task_type": "build_exit_intents", "input_path": str(exit_ast),
            "output_path": str(exit_intents), "output": "exit_intent",
            "condition": {"schema_version": 1, "side": "long", "exit": {"signal": {"series": "exit_signal", "type": "boolean"}, "timing": "next_open"}},
        })
        simulation = _run_task(work, "simulation", {
            "task_version": 1, "task_type": "simulate_market_v1", "market_path": str(SOURCE),
            "entry_intent_path": str(entry_intents), "exit_intent_path": str(exit_intents),
            "output_path": str(trades), "config": {
                "schema_version": 1, "side": "long", "price_column": "open",
                "entry_column": "entry_intent", "exit_column": "exit_intent",
                "position_policy": "one_at_a_time", "terminal_policy": "leave_open",
                "initial_bracket": {"model": "fixed_price_offsets_v1", "stop_offset": 0.0005, "target_offset": 0.0008, "output_path": str(work / "brackets.parquet")},
                "initial_bracket_execution": {"model": "ohlc_unambiguous_v1", "event_output_path": str(work / "events.parquet")},
            },
        })
        metric = _run_task(work, "metrics", {
            "task_version": 1, "task_type": "compute_closed_trade_metrics_v1",
            "input_path": str(trades), "output_path": str(metrics),
        })
        metrics_value = json.loads(metrics.read_text())

    body = {
        "schema_version": SCHEMA,
        "source_fixture": "tests/fixtures/phase2_linux_replay_m1.parquet",
        "stages": {
            "ingestion": {"task_type": ingestion["task_type"], "rows": ingestion["rows"], "semantic_content_identity": ingestion["semantic_content_identity"]},
            "aggregation": {"task_type": aggregation["task_type"], "input_identity": aggregation["source_semantic_content_identity"], "output_identity": aggregation["output_semantic_content_identity"], "rows": aggregation["output_rows"]},
            "indicators": {"task_type": indicator["task_type"], "input_identity": ingestion["semantic_content_identity"], "output_identity": indicator["output_semantic_content_identity"], "rows": indicator["rows"], "input_contract": "canonical_m1_branch"},
            "ast_intents": {"entry_ast_identity": entry_eval["ast_semantic_identity"], "exit_ast_identity": exit_eval["ast_semantic_identity"], "entry_evaluated_identity": entry_eval["evaluated_artifact_semantic_identity"], "exit_evaluated_identity": exit_eval["evaluated_artifact_semantic_identity"], "entry_intent_identity": entry["entry_intent_semantic_identity"], "exit_intent_identity": exit_["exit_intent_semantic_identity"]},
            "simulation": {"task_type": simulation["task_type"], "output_identity": simulation["simulator_semantic_identity"], "trades_closed": simulation["trades_closed"]},
            "metrics": {"task_type": metric["task_type"], "output_identity": metric["metrics_semantic_identity"], "metrics": metrics_value},
        },
    }
    body["trades"] = {"trade_count": body["stages"]["metrics"]["metrics"]["trade_count"], "identity": body["stages"]["simulation"]["output_identity"]}
    body["classification"] = "PASS_LINUX_EXPERIMENT_REPLAY"
    body["replay_identity"] = sha(body)
    return body


def run_linux_replay() -> dict[str, Any]:
    return _body()


def verify_linux_replay(value: dict[str, Any]) -> bool:
    if not isinstance(value, dict) or value.get("replay_identity") != sha({k: v for k, v in value.items() if k != "replay_identity"}):
        raise ValueError("Linux replay identity mismatch")
    if value.get("classification") != "PASS_LINUX_EXPERIMENT_REPLAY":
        raise ValueError("Linux replay is not a pass")
    if value.get("trades", {}).get("trade_count", 0) < 1:
        raise ValueError("Linux replay has no closed trade")
    return True
