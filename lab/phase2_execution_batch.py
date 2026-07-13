"""Generated, fail-closed local-native batch contract for the execution canary."""
from __future__ import annotations

import json
import hashlib
import shutil
import tempfile
from pathlib import Path

from lab.mql5gen.execution import PACKAGE, RUNTIME, TESTER, generate
from lab.phase2_execution import canon, sha

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "tests/fixtures/phase2x_native_batch_v4.json"
EVIDENCE = "tests/fixtures/phase2_execution_rust_evidence.json"
VERSION = "nora.phase2x.execution_native_batch_v5"
HISTORICAL_BATCH = "44be335b8f517fbdfb4de7d9d4b5e1f42f80e0d7dd636659dfd1c4f2b98f458c"
HISTORICAL_TESTER = "c09086906c22972b384970cbd66fd6d78c757e74d618499ec1f4e8ece81cd188"
HISTORICAL_PACKAGE = "00e87549f0d08843a2ab35c7d4342d498f293bac488d553b018104370ee25258"
SCRIPT_PATHS = (
    "phase-0a-h/windows/compile-execution-tester-canary.ps1",
    "phase-0a-h/windows/execute-execution-tester-canary.ps1",
    "phase-0a-h/windows/build-execution-returned-package.ps1",
)
GENERATED_ROOT = "generated/phase2_execution"
FAILURES = [
    "wrong_entry_bar", "wrong_entry_price", "wrong_exit_bar", "wrong_exit_price",
    "wrong_exit_reason", "precedence_failure", "ambiguous_bar_optimism",
    "same_bar_entry_exit", "missing_ledger_row", "extra_ledger_row",
    "duplicate_scenario", "scenario_reordering", "incomplete_result",
    "compiler_failure", "runtime_failure", "interrupted_result", "identity_failure",
    "contract_failure",
]


def _file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _bytes_sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _generated() -> tuple[dict, dict[str, bytes]]:
    """Generate in a private fresh directory and return only deterministic bytes."""
    with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
        out = Path(tmp) / "generated"
        out.mkdir()
        package = generate(ROOT / EVIDENCE, out)
        return package, {name: (out / name).read_bytes() for name in (RUNTIME, TESTER, PACKAGE)}


def build() -> dict:
    package, generated = _generated()
    evidence = json.loads((ROOT / EVIDENCE).read_text())
    generated_paths = {name: f"{GENERATED_ROOT}/{name}" for name in generated}
    files = [
        {"path": EVIDENCE, "sha256": _file_sha(ROOT / EVIDENCE), "role": "rust_execution_evidence"},
        *[
            {"path": generated_paths[name], "sha256": _bytes_sha(data), "role": role}
            for name, data, role in (
                (RUNTIME, generated[RUNTIME], "mql5_runtime"),
                (TESTER, generated[TESTER], "mql5_tester"),
                (PACKAGE, generated[PACKAGE], "executable_package"),
            )
        ],
        *[
            {"path": path, "sha256": _file_sha(ROOT / path), "role": role}
            for path, role in zip(SCRIPT_PATHS, ("compiler_script", "execution_script", "package_builder_script"))
        ],
    ]
    execution = {
        "id": "execution",
        "rust_evidence": EVIDENCE,
        "execution_plan_identity": evidence["execution_plan_identity"],
        "scenario_identities": {x["scenario_id"]: x["scenario_identity"] for x in evidence["scenarios"]},
        "runtime_identity": package["runtime_identity"],
        "runtime_sha256": package["runtime_sha256"],
        "tester_identity": package["tester_identity"],
        "tester_sha256": package["tester_sha256"],
        "package_identity": package["package_identity"],
        "expected_execution_vector_identity": package["expected_execution_vector_identity"],
        "execution_csv_schema_identity": package["execution_csv_schema_identity"],
        "result_filename": package["result_filename"],
        "completion_marker": package["completion_marker"],
        "failure_marker": package["failure_marker"],
        "precedence_contract": package["precedence_contract"],
        "host_contexts": ["GDAXI/M1", "AUDCAD/M1"],
        "required_native_matrix": ["compile", "gdaxi_m1_1", "gdaxi_m1_2", "audcad_m1_1", "audcad_m1_2"],
        "files": files,
        "native_execution_attempted": False,
        "native_result_returned": False,
        "native_reconciliation_passed": False,
        "native_parity_evidence_available": False,
        "native_parity_accepted": False,
        "grammar_admitted": False,
        "searchable": False,
    }
    allowlisted_paths = [MANIFEST] + [f["path"] for f in files]
    # v5 deliberately binds roles and paths, not content.  Content is instead bound
    # by each file hash and the batch identity; this avoids a self-referential manifest.
    staged_inventory = [{"path": f["path"], "role": f["role"]} for f in files]
    value = {
        "schema_version": VERSION,
        "supersedes": "tests/fixtures/phase2x_native_batch_v4.json",
        "historical_batch_identities": [HISTORICAL_BATCH],
        "superseded_execution_identities": {"tester": [HISTORICAL_TESTER], "package": [HISTORICAL_PACKAGE]},
        "target_order": ["execution"],
        "execution": execution,
        "allowlisted_paths": allowlisted_paths,
        "staged_inventory_definition": "nora.phase2x.execution_roles_paths_v1",
        "staged_inventory_identity": sha(staged_inventory),
    }
    value["batch_identity"] = sha(value)
    return value


def load(path: str = MANIFEST) -> dict:
    return json.loads((ROOT / path).read_text())


def write_manifest(path: str = MANIFEST) -> dict:
    value = build()
    target = ROOT / path
    tmp = target.with_suffix(target.suffix + ".tmp")
    try:
        tmp.write_bytes((canon(value) + "\n").encode())
        tmp.replace(target)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    return value


def preflight_batch(value: dict) -> str:
    try:
        expected = build()
    except Exception:
        return "generation_failure"
    if value != expected:
        return "stale_or_mixed_identity_chain"
    e = value.get("execution", {})
    if any(e.get(k) for k in ("native_execution_attempted", "native_result_returned", "native_reconciliation_passed", "native_parity_evidence_available", "native_parity_accepted", "grammar_admitted", "searchable")):
        return "state_failure"
    return "ok"


def preflight(path: str = MANIFEST) -> dict:
    value = load(path)
    status = preflight_batch(value)
    return {"status": "PASS" if status == "ok" else "FAIL", "classification": status,
            "batch_identity": value.get("batch_identity"), "staged_inventory_identity": value.get("staged_inventory_identity")}


def stage(destination: Path) -> dict:
    destination = Path(destination)
    if destination.exists():
        raise ValueError("existing destination")
    value = load()
    if preflight_batch(value) != "ok":
        raise ValueError("preflight")
    package, generated = _generated()
    temporary = Path(tempfile.mkdtemp(prefix=".phase2-execution-stage-", dir=destination.parent))
    try:
        for item in value["execution"]["files"]:
            path = item["path"]
            target = temporary / path
            target.parent.mkdir(parents=True, exist_ok=True)
            if path.startswith(GENERATED_ROOT + "/"):
                target.write_bytes(generated[Path(path).name])
            else:
                shutil.copy2(ROOT / path, target)
            if _file_sha(target) != item["sha256"]:
                raise ValueError("staging hash mismatch: " + path)
        (temporary / MANIFEST).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / MANIFEST, temporary / MANIFEST)
        temporary.replace(destination)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return {"batch_identity": value["batch_identity"], "staged_inventory_identity": value["staged_inventory_identity"], "package_identity": package["package_identity"]}


def classify_synthetic(kind: str) -> str:
    return kind if kind in FAILURES else "exact_pass"
