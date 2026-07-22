"""Canonical trade-ledger reconciliation for the sealed ten-strategy smoke package."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from lab.phase2_execution import canon, sha
from lab.phase2_ten_strategy_native import (
    NUMERIC,
    STRUCTURAL,
    budget_map,
    expected_rows,
    reconcile_rows,
    reconciliation_protocol,
)
from lab.phase2_ten_strategy_v2 import _parse_csv

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/phase2_ten_strategy_suite"
NATIVE = FIXTURE / "native_four_context_accepted"
CSV_NAME = "nora_phase2_ten_strategy_v1.csv"
CONTEXTS = ("A1", "A2", "B1", "B2")
TRADE_FIELDS = tuple(STRUCTURAL) + tuple(NUMERIC)


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reconcile_native_context(context_dir: Path) -> dict:
    """Reconcile one raw native CSV against the sealed Rust trade ledger."""
    context_dir = Path(context_dir)
    csv_path = context_dir / CSV_NAME
    if not csv_path.is_file():
        raise ValueError(f"missing native CSV: {csv_path}")
    rows = _parse_csv(csv_path)
    expected = expected_rows()
    if len(rows) != len(expected):
        raise ValueError("ROW_COUNT_MISMATCH")
    result = reconcile_rows(rows)
    for ordinal, (actual, reference) in enumerate(zip(rows, expected), start=1):
        for field in TRADE_FIELDS:
            if actual.get(field) != reference.get(field):
                raise ValueError(f"TRADE_FIELD_MISMATCH:{ordinal}:{field}")
    return {
        "classification": result["classification"],
        "row_count": len(rows),
        "reconciliation_identity": result["reconciliation_identity"],
        "csv_sha256": _file_sha256(csv_path),
        "trade_fields_reconciled": list(TRADE_FIELDS),
        "budget_map_identity": result["budget_map_identity"],
    }


def _raw_evidence_hashes(context: str) -> dict[str, str]:
    context_dir = NATIVE / context.lower()
    native_manifest = json.loads(
        (NATIVE / "native_acceptance_manifest.json").read_text(encoding="utf-8")
    )
    entry = next(item for item in native_manifest["contexts"] if item["context"] == context)
    hashes = {}
    for name in entry["files"]:
        path = context_dir / name
        if not path.is_file():
            raise ValueError(f"missing raw native evidence: {path}")
        actual = _file_sha256(path)
        if actual != entry["files"][name]:
            raise ValueError(f"raw native evidence hash mismatch: {context}/{name}")
        hashes[name] = actual
    return hashes


def build_manifest() -> dict:
    """Build the identity-bound E2 manifest from raw evidence and frozen ledgers."""
    native_manifest_path = NATIVE / "native_acceptance_manifest.json"
    native_manifest = json.loads(native_manifest_path.read_text(encoding="utf-8"))
    if native_manifest["classification"] != "system_smoke_not_edge_claim":
        raise ValueError("unexpected native acceptance classification")
    if native_manifest["all_reconciliations"] != "PASS_EXACT":
        raise ValueError("native smoke summary is not PASS_EXACT")

    protocol = json.loads((FIXTURE / "reconciliation_protocol.json").read_text())
    budgets = json.loads((FIXTURE / "budget_map.json").read_text())
    rust = json.loads((FIXTURE / "rust_evidence.json").read_text())
    runs = {}
    for context in CONTEXTS:
        result = reconcile_native_context(NATIVE / context.lower())
        result["run_identifier"] = next(
            item["run_identifier"]
            for item in native_manifest["contexts"]
            if item["context"] == context
        )
        result["raw_evidence_sha256"] = _raw_evidence_hashes(context)
        runs[context] = result

    identities = {run["reconciliation_identity"] for run in runs.values()}
    csv_hashes = {run["csv_sha256"] for run in runs.values()}
    body = {
        "schema_version": "nora.phase2.strategy_trade_reconciliation_v1",
        "classification": "PASS_EXACT",
        "scope": "embedded ten-strategy suite only; not finalist edge proof",
        "strategy_count": 10,
        "trade_count_per_context": len(expected_rows()),
        "trade_fields": list(TRADE_FIELDS),
        "protocol_identity": protocol["strategy_reconciliation_protocol_identity"],
        "budget_map_identity": budgets["applicable_budget_map_identity"],
        "rust_evidence_identity": rust["combined_rust_evidence_identity"],
        "native_acceptance_manifest_sha256": _file_sha256(native_manifest_path),
        "native_acceptance_classification": native_manifest["classification"],
        "contexts": list(CONTEXTS),
        "runs": runs,
        "cross_context_equivalence": len(identities) == 1 and len(csv_hashes) == 1,
        "grammar_admitted": False,
        "searchable": False,
        "phase3_authorized": False,
        "complete_phase2_gate": False,
    }
    body["trade_reconciliation_identity"] = sha(body)
    return body


if __name__ == "__main__":
    print(canon(build_manifest()))
