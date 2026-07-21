import json, subprocess, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "engine" / "target" / "debug" / "labengine"
FIXTURE = ROOT / "tests" / "fixtures" / "phase2_stochastic_scenarios.json"


def test_rust_layer1_task_emits_deterministic_stochastic_k_and_d_rows():
    source = json.loads(FIXTURE.read_text())
    task = {"task_version": 1, "task_type": "layer1_parity_v1", "scenarios": source["scenarios"]}
    with tempfile.TemporaryDirectory() as directory:
        task_path = Path(directory) / "task.json"
        task_path.write_text(json.dumps(task))
        result = subprocess.run([str(ENGINE), str(task_path)], text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["ok"] is True
    assert {row["node"] for row in output["rows"]} == {"Stochastic"}
    ordinary = [row for row in output["rows"] if row["scenario_id"] == "ordinary_kd"]
    assert any(row["output"] == "k" and row["classification"] == "steady_state" for row in ordinary)
    assert any(row["output"] == "d" and row["classification"] == "steady_state" for row in ordinary)
    zero = [row for row in output["rows"] if row["scenario_id"] == "zero_range" and row["output"] == "k"]
    assert any(row["value"] == 50.0 for row in zero)
    assert any(row["reason_code"] == "invalid_period" for row in output["rows"])


def test_stochastic_package_builder_is_deterministic_and_native_open():
    from lab.mql5gen.stochastic_batch import generate

    evidence = json.loads((ROOT / "tests/fixtures/phase2_stochastic_local_evidence/rust_evidence.json").read_text())
    with tempfile.TemporaryDirectory() as left, tempfile.TemporaryDirectory() as right:
        a = generate(Path(left), evidence)
        b = generate(Path(right), evidence)
    assert a == b
    assert a["package_identity"] == "cbe733484749e64d84333409acc1e110d38b97b5a1c1e0d9b5ef969e4fe9f8bb"
    assert a["target_identifier"] == "layer1_stochastic"
    assert a["native_execution_attempted"] is False
    assert a["native_parity_accepted"] is False
    assert a["grammar_admitted"] is False
    assert a["searchable"] is False
    committed = json.loads((ROOT / "tests/fixtures/phase2_stochastic_native/phase2_stochastic_executable_package.json").read_text())
    assert committed == a
