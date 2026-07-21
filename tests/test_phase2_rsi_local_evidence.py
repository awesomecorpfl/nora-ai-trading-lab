import json, subprocess, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "engine" / "target" / "debug" / "labengine"
FIXTURE = ROOT / "tests" / "fixtures" / "phase2_rsi_scenarios.json"


def test_rust_layer1_task_emits_deterministic_rsi_rows():
    source = json.loads(FIXTURE.read_text())
    task = {"task_version": 1, "task_type": "layer1_parity_v1", "scenarios": source["scenarios"]}
    with tempfile.TemporaryDirectory() as directory:
        task_path = Path(directory) / "task.json"
        task_path.write_text(json.dumps(task))
        result = subprocess.run([str(ENGINE), str(task_path)], text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["ok"] is True
    assert {row["node"] for row in output["rows"]} == {"RSI"}
    assert any(row["classification"] == "steady_state" for row in output["rows"])
    assert any(row["reason_code"] == "invalid_period" for row in output["rows"])


def test_frozen_rsi_evidence_identity_is_present_and_nonsearchable():
    evidence = json.loads((ROOT / "tests/fixtures/phase2_rsi_local_evidence/rust_evidence.json").read_text())
    assert evidence["rust_evidence_identity"] == "897290757d5898fd0a5edcc41fc6b2f24af2ec9d851bef9cbeb9e8d2d283dfe5"
    assert evidence["expected_vector_identity"] == "9fa287b90a2c8cba30f2c13a8be0a1a6194f70fc9d76cb4d4c899b5592c8aea6"
    assert evidence["grammar_admitted"] is False
    assert evidence["searchable"] is False
