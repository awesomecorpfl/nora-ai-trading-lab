import json
from pathlib import Path

import pyarrow.parquet as pq

from lab.phase2_execution_strategy import CASE, _write_inputs
from lab.phase2_execution_strategy import run_execution_strategy, verify_execution_strategy


ROOT = Path(__file__).resolve().parents[1]


def test_local_execution_strategy_generator_reconciles_one_entry_and_one_exit():
    result = run_execution_strategy()
    assert verify_execution_strategy(result)
    assert result["classification"] == "PASS_LOCAL_EXECUTION_STRATEGY_RECONCILIATION"
    assert result["reconciliation"]["expected_trade_count"] == 1
    assert result["reconciliation"]["actual_trade_count"] == 1
    assert result["reconciliation"]["expected_exit_reason"] == "signal"
    assert result["reconciliation"]["actual_exit_reason"] == "signal"


def test_committed_execution_strategy_fixture_matches_runtime():
    fixture = ROOT / "tests/fixtures/phase2_local_execution_strategy_fixture.json"
    committed = json.loads(fixture.read_text())
    assert committed == run_execution_strategy()
    assert verify_execution_strategy(committed)


def test_generated_market_materializes_complete_ohlc_bars(tmp_path):
    paths = _write_inputs(tmp_path)
    table = pq.read_table(paths["market"])
    assert table.column_names == ["timestamp", "open", "high", "low", "close"]
    assert table["close"].to_pylist() == [bar["close"] for bar in CASE["bars"]]
