import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/phase2_stochastic_native"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_stochastic_native_manifest_is_exact_and_four_contexts_reconcile():
    manifest = json.loads((FIXTURE / "native_evidence_manifest.json").read_text())
    expected = json.loads(
        (ROOT / "tests/fixtures/phase2_stochastic_local_evidence/rust_evidence.json").read_text()
    )["rust_output"]["rows"]
    assert manifest["acceptance"] == "PASS_EXACT"
    assert manifest["native_parity_accepted"] is True
    assert manifest["compiled"] == {
        "status": "compiled",
        "errors": 0,
        "warnings": 0,
        "ex5_path": "compile/NoraPhase2StochasticTesterV1.ex5",
        "ex5_sha256": sha256(FIXTURE / "compile/NoraPhase2StochasticTesterV1.ex5"),
        "compile_log_sha256": sha256(FIXTURE / "compile/compile.log"),
    }
    csv_hashes = set()
    for label, binding in manifest["contexts"].items():
        run = FIXTURE / "runs" / label
        execution = json.loads((run / "execution.json").read_text(encoding="utf-8-sig"))
        rows = list(csv.DictReader((run / "nora_phase2_stochastic_v1.csv").open(encoding="utf-8-sig"), delimiter="\t"))
        assert execution["status"] == "completed"
        assert execution["native_process_exit_status"] == 0
        assert execution["completion_marker_present"] is True
        assert execution["failure_marker_present"] is False
        assert len(rows) == len(expected) == 18
        assert sha256(run / "execution.json") == binding["execution_sha256"]
        assert sha256(run / "nora_phase2_stochastic_v1.csv") == binding["csv_sha256"]
        csv_hashes.add(binding["csv_sha256"])
        for got, want in zip(rows, expected):
            assert got["scenario_id"] == want["scenario_id"]
            assert got["node"] == want["node"] == "Stochastic"
            assert got["output"] == want["output"]
            if want["row"] is None:
                assert got["row"] == "NULL"
            else:
                assert int(got["row"]) == want["row"]
            if want["timestamp"] is None:
                assert got["timestamp"] == "NULL"
            else:
                assert got["timestamp"] == want["timestamp"]
            assert got["null"] == ("true" if want["null"] else "false")
            assert got["classification"] == want["classification"]
            assert got["reason_code"] == want["reason_code"]
            if want["value"] is None:
                assert got["value"] == "NULL"
            else:
                assert abs(float(got["value"]) - want["value"]) == 0.0
        normalized = (run / "tester.ini.normalized").read_text()
        assert "<redacted>" in normalized
        assert "Login=" not in normalized or "Login=<redacted>" in normalized
        assert "Server=" not in normalized or "Server=<redacted>" in normalized
    assert csv_hashes == {"4e8ac3322f0ba95790d76da77c8e36490f00065623f0bb202a03fe48000ef2a9"}
    assert manifest["cross_context_csv_sha256_equal"] is True
