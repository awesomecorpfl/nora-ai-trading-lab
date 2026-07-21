import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "tests/fixtures/phase2_adx_native"
MANIFEST = BASE / "native_evidence_manifest.json"
EVIDENCE = ROOT / "tests/fixtures/phase2_adx_local_evidence/rust_evidence.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_adx_native_evidence_is_complete_and_exact():
    manifest = json.loads(MANIFEST.read_text())
    expected = json.loads(EVIDENCE.read_text())["rust_output"]["rows"]
    assert manifest["acceptance"] == "PASS_EXACT"
    assert manifest["native_parity_accepted"] is True
    assert manifest["compiled"]["errors"] == 0
    assert manifest["compiled"]["warnings"] == 0
    assert digest(BASE / manifest["compiled"]["ex5_path"]) == manifest["compiled"]["ex5_sha256"]
    assert digest(BASE / "compile/adx-compile.log") == manifest["compiled"]["compile_log_sha256"]
    csv_hashes = []
    for key, context in manifest["contexts"].items():
        run = BASE / "runs" / context["run_id"]
        execution = json.loads((run / "execution.json").read_text(encoding="utf-8-sig"))
        rows = list(csv.DictReader((run / "nora_phase2_adx_v1.csv").open(encoding="utf-8-sig"), delimiter="\t"))
        assert execution["status"] == "completed"
        assert execution["native_process_exit_status"] == 0
        assert execution["completion_marker_present"] is True
        assert execution["failure_marker_present"] is False
        assert len(rows) == len(expected) == context["rows"]
        assert digest(run / "execution.json") == context["execution_sha256"]
        assert digest(run / "tester.ini.normalized") == context["tester_ini_normalized_sha256"]
        assert digest(run / "nora_phase2_adx_v1.csv") == context["csv_sha256"]
        csv_hashes.append(context["csv_sha256"])
        for got, want in zip(rows, expected):
            assert got["scenario_id"] == want["scenario_id"]
            assert got["output"] == want["output"]
            assert got["row"] == ("NULL" if want["row"] is None else str(want["row"]))
            assert got["timestamp"] == ("NULL" if want["timestamp"] is None else want["timestamp"])
            assert got["null"] == str(want["null"]).lower()
            if want["value"] is None:
                assert got["value"] == "NULL"
            else:
                assert abs(float(got["value"]) - want["value"]) <= 1e-12
    assert len(set(csv_hashes)) == 1
    assert manifest["cross_context_csv_sha256_equal"] is True
