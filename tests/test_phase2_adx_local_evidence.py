import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "engine" / "target" / "debug" / "labengine"
FIXTURE = ROOT / "tests/fixtures/phase2_adx_scenarios.json"


def test_rust_layer1_task_emits_deterministic_adx_rows():
    source = json.loads(FIXTURE.read_text())
    task = {"task_version": 1, "task_type": "layer1_parity_v1", "scenarios": source["scenarios"]}
    with tempfile.TemporaryDirectory() as directory:
        task_path = Path(directory) / "task.json"
        task_path.write_text(json.dumps(task))
        result = subprocess.run([str(ENGINE), str(task_path)], text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["ok"] is True
    assert len(output["rows"]) == 22
    assert {row["node"] for row in output["rows"]} == {"ADX"}
    trend = [row for row in output["rows"] if row["scenario_id"] == "directional_trend"]
    assert any(row["value"] == 100.0 for row in trend)
    mixed = [row for row in output["rows"] if row["scenario_id"] == "mixed_direction"]
    assert any(row["classification"] == "steady_state" for row in mixed)
    zero = [row for row in output["rows"] if row["scenario_id"] == "zero_denominator"]
    assert all(row["value"] is None for row in zero)
    assert any(row["reason_code"] == "invalid_period" for row in output["rows"])


def test_adx_package_builder_is_deterministic_and_native_open():
    from lab.mql5gen.adx_batch import generate

    evidence = json.loads((ROOT / "tests/fixtures/phase2_adx_local_evidence/rust_evidence.json").read_text())
    with tempfile.TemporaryDirectory() as left, tempfile.TemporaryDirectory() as right:
        a = generate(Path(left), evidence)
        b = generate(Path(right), evidence)
    assert a == b
    assert a["package_identity"] == "76abc8b04292faca720bbef351e777dc6e14ba22b64c56e57cae6ab5c23f75a4"
    assert a["target_identifier"] == "layer1_adx"
    assert a["native_execution_attempted"] is False
    assert a["native_parity_accepted"] is False
    assert a["grammar_admitted"] is False
    assert a["searchable"] is False
    committed = json.loads((ROOT / "tests/fixtures/phase2_adx_native/phase2_adx_executable_package.json").read_text())
    assert committed == a
