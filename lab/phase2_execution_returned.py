"""Strict ingestion and reconciliation for native execution-canary packages."""
from __future__ import annotations

import csv
import argparse
import hashlib
import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

from lab.phase2_execution import canon, sha

CSV_NAME = "nora_phase2_execution_tester_v1.csv"
REQUIRED = (
    "compile.json", "execution.json", "compile.log", "tester-journal.log",
    "tester.htm", "completion-marker.json", "failure-marker.json", CSV_NAME,
)
ABS_TOL = 1e-12
REL_TOL = 1e-9


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _expected_rows(evidence: dict) -> list[dict]:
    rows = []
    for index, scenario in enumerate(evidence["scenarios"]):
        fixture = scenario["task_fixture"]
        trade = scenario["expected_trade_ledger_rows"]
        if not trade:
            rows.append({"scenario_id": scenario["scenario_id"], "ledger_row_index": index,
                         "entry_bar_index": None, "entry_price": None, "exit_bar_index": None,
                         "exit_price": None, "direction": fixture["side"], "stop_price": None,
                         "target_price": None, "exit_reason": "no_trade",
                         "expected_state": "no_trade", "pass": "true"})
            continue
        ledger = trade[0]
        rows.append({"scenario_id": scenario["scenario_id"], "ledger_row_index": index,
                     "entry_bar_index": ledger["entry_index"], "entry_price": ledger["entry_price"],
                     "exit_bar_index": ledger["exit_index"], "exit_price": ledger["exit_price"],
                     "direction": ledger["side"],
                     "stop_price": ledger["entry_price"] - fixture["stop_offset"],
                     "target_price": ledger["entry_price"] + fixture["target_offset"],
                     "exit_reason": scenario["exit_reason"], "expected_state": "trade", "pass": "true"})
    return rows


def _actual_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        raw = list(csv.DictReader(stream, delimiter="\t"))
    integer = {"ledger_row_index", "entry_bar_index", "exit_bar_index"}
    numeric = {"entry_price", "exit_price", "stop_price", "target_price"}
    result = []
    for source in raw:
        row = {}
        for key, value in source.items():
            if value == "NULL": row[key] = None
            elif key in integer: row[key] = int(value)
            elif key in numeric: row[key] = float(value)
            else: row[key] = value
        result.append(row)
    return result


def ingest(package_dir: Path, packet: dict, batch: dict, evidence: dict,
           expected_run: str, expected_symbol: str) -> dict:
    package_dir = Path(package_dir)
    expected_files = set(REQUIRED) | {"returned_inventory.json", "returned_result_manifest.json"}
    if {p.name for p in package_dir.iterdir() if p.is_file()} != expected_files:
        raise ValueError("package file set")
    manifest = load_json(package_dir / "returned_result_manifest.json")
    package_identity = manifest.pop("returned_package_identity", None)
    encoded = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False).encode()
    if package_identity != hashlib.sha256(encoded).hexdigest(): raise ValueError("package identity")
    manifest["returned_package_identity"] = package_identity
    inventory_path = package_dir / "returned_inventory.json"
    if file_sha(inventory_path) != manifest["returned_inventory_sha256"]: raise ValueError("inventory identity")
    inventory = load_json(inventory_path)
    if [x.get("path") for x in inventory] != list(REQUIRED): raise ValueError("inventory order")
    for item in inventory:
        path = package_dir / item["path"]
        if path.stat().st_size != item["size"] or file_sha(path) != item["sha256"]:
            raise ValueError("inventory binding")
    record = load_json(package_dir / "execution.json")
    required_bindings = {
        "run_identifier": expected_run, "host_symbol": expected_symbol, "timeframe": "M1",
        "final_batch_identity": batch["final_batch_identity"],
        "compile_input_identity": packet["compile_input_identity"],
        "compiler_output_identity": packet["compiler_output_identity"],
        "execution_packet_identity": packet["execution_packet_identity"],
        "ex5_sha256": packet["ex5_sha256"], "runtime_identity": packet["runtime_identity"],
        "tester_identity": packet["tester_identity"], "package_identity": packet["package_identity"],
        "execution_plan_identity": packet["execution_plan_identity"],
        "expected_vector_identity": packet["expected_vector_identity"],
        "csv_schema_identity": packet["csv_schema_identity"], "collection_state": "complete",
        "completion_marker_present": True, "failure_marker_present": False,
        "no_trading_operations": True, "process_exit": 0,
    }
    if any(record.get(k) != v for k, v in required_bindings.items()): raise ValueError("execution binding")
    if datetime.fromisoformat(record["requested_start_utc"].replace("Z", "+00:00")) >= datetime.fromisoformat(record["observed_completion_utc"].replace("Z", "+00:00")):
        raise ValueError("run chronology")
    if record["result_csv_sha256"] != file_sha(package_dir / CSV_NAME): raise ValueError("csv record")
    if record["journal_segment_sha256"] != file_sha(package_dir / "tester-journal.log"): raise ValueError("journal record")
    complete = load_json(package_dir / "completion-marker.json")
    failure = load_json(package_dir / "failure-marker.json")
    if complete != {"present": True, "marker": packet["completion_marker"]}: raise ValueError("completion marker")
    if failure != {"present": False, "marker": packet["failure_marker"]}: raise ValueError("failure marker")
    report = load_json(package_dir / "tester.htm")
    if any((report.get(k) != v for k, v in {"run_identifier": expected_run, "symbol": expected_symbol,
            "timeframe": "M1", "ex5_sha256": packet["ex5_sha256"],
            "csv_sha256": record["result_csv_sha256"], "journal_sha256": record["journal_segment_sha256"],
            "completion_marker_present": True, "failure_marker_present": False,
            "no_trading_operations": True}.items())): raise ValueError("tester evidence")
    compiler = load_json(package_dir / "compile.json")
    if sha(compiler) != packet["compiler_output_identity"] or compiler.get("ex5_sha256") != packet["ex5_sha256"]:
        raise ValueError("compiler binding")
    actual, expected = _actual_rows(package_dir / CSV_NAME), _expected_rows(evidence)
    if len(actual) != len(expected): raise ValueError("ledger row count")
    maxima = {key: {"absolute": 0.0, "relative": 0.0} for key in ("entry_price", "exit_price", "stop_price", "target_price")}
    exact = True
    decision = ("scenario_id", "ledger_row_index", "entry_bar_index", "exit_bar_index",
                "direction", "exit_reason", "expected_state", "pass")
    for got, want in zip(actual, expected):
        if any(got[key] != want[key] for key in decision): raise ValueError("decision mismatch")
        for key in maxima:
            if (got[key] is None) != (want[key] is None): raise ValueError("null mismatch")
            if got[key] is None: continue
            absolute = abs(got[key] - want[key]); relative = absolute / max(abs(want[key]), 1e-15)
            maxima[key]["absolute"] = max(maxima[key]["absolute"], absolute)
            maxima[key]["relative"] = max(maxima[key]["relative"], relative)
            if absolute > ABS_TOL + REL_TOL * abs(want[key]): raise ValueError("price mismatch")
            exact &= absolute == 0.0
    result = {
        "schema_version": "nora.execution_native_reconciliation_v1", "run_identifier": expected_run,
        "host_context": f"{expected_symbol}/M1", "returned_package_identity": package_identity,
        "returned_inventory_identity": file_sha(inventory_path),
        "execution_record_identity": sha(record), "csv_sha256": file_sha(package_dir / CSV_NAME),
        "journal_segment_identity": file_sha(package_dir / "tester-journal.log"),
        "tester_report_substitute_identity": file_sha(package_dir / "tester.htm"),
        "classification": "PASS_EXACT" if exact else "PASS_WITHIN_TOLERANCE",
        "price_divergence": maxima, "semantic_ledger_identity": sha(actual),
    }
    result["reconciliation_identity"] = sha(result)
    return result


def publish_acceptance(source: Path, final_dir: Path, destination: Path) -> dict:
    source, final_dir, destination = Path(source), Path(final_dir), Path(destination)
    if destination.exists(): raise ValueError("occupied acceptance destination")
    packet = load_json(final_dir / "execution_packet.json")
    batch = load_json(final_dir / "final_batch.json")
    evidence = load_json(Path(__file__).resolve().parents[1] / "tests/fixtures/phase2_execution_rust_evidence.json")
    cases = [("A1", "GDAXI"), ("A2", "GDAXI"), ("B1", "AUDCAD"), ("B2", "AUDCAD")]
    results = [ingest(source / f"exec-0c13771-{case}", packet, batch, evidence,
                      f"exec-0c13771-{case}", symbol) for case, symbol in cases]
    if {x["classification"] for x in results} - {"PASS_EXACT", "PASS_WITHIN_TOLERANCE"}:
        raise ValueError("reconciliation failed")
    if len({x["returned_package_identity"] for x in results}) != 4 or len({x["execution_record_identity"] for x in results}) != 4:
        raise ValueError("run independence")
    if len({x["semantic_ledger_identity"] for x in results}) != 1:
        raise ValueError("host neutrality")
    compiler = load_json(final_dir / "compile/compiler_record.json")
    acceptance = {
        "schema_version": "nora.execution_native_acceptance_v1",
        "compile_input_identity": packet["compile_input_identity"],
        "compiler_output_identity": packet["compiler_output_identity"],
        "compiler_log_identity": packet["compiler_log_sha256"],
        "compiler_policy": compiler["compiler_policy"], "compiler_raw_exit": compiler["raw_process_exit"],
        "compiler_normalized_result": compiler["policy_decision"],
        "compiler_errors": compiler["error_count"], "compiler_warnings": compiler["warning_count"],
        "ex5_sha256": packet["ex5_sha256"], "ex5_size": packet["ex5_size"],
        "execution_packet_identity": packet["execution_packet_identity"],
        "final_native_batch_identity": batch["final_batch_identity"],
        "staged_inventory_identity": batch["staged_inventory_identity"],
        "execution_plan_identity": packet["execution_plan_identity"],
        "expected_vector_identity": packet["expected_vector_identity"],
        "csv_schema_identity": packet["csv_schema_identity"],
        "scenario_identities": packet["scenario_identities"], "runs": results,
        "all_runs_independently_fresh": True, "within_context_repeatability": True,
        "cross_context_neutrality": True, "native_execution_attempted": True,
        "native_result_returned": True, "native_reconciliation_passed": True,
        "native_parity_evidence_available": True, "native_parity_accepted": True,
        "grammar_admitted": False, "searchable": False, "complete_phase2_gate": False,
    }
    acceptance["acceptance_identity"] = sha(acceptance)
    temporary = Path(tempfile.mkdtemp(prefix=".execution-native-acceptance-", dir=destination.parent))
    try:
        for index, (case, _) in enumerate(cases):
            shutil.copytree(source / f"exec-0c13771-{case}", temporary / case.lower())
            (temporary / f"reconciliation-{case.lower()}.json").write_text(canon(results[index]) + "\n")
        shutil.copytree(final_dir / "compile", temporary / "compile")
        for name in ("compile_input.json", "execution_packet.json", "final_batch.json"):
            shutil.copy2(final_dir / name, temporary / name)
        (temporary / "native_acceptance.json").write_text(canon(acceptance) + "\n")
        temporary.replace(destination)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True); raise
    return acceptance


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--source", required=True)
    parser.add_argument("--final-dir", required=True); parser.add_argument("--destination", required=True)
    args = parser.parse_args()
    result = publish_acceptance(Path(args.source), Path(args.final_dir), Path(args.destination))
    print(canon(result)); return 0


if __name__ == "__main__": raise SystemExit(main())
