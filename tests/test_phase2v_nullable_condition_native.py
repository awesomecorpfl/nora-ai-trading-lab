"""RED acceptance boundary for the bounded Phase-2 nullable condition gate.

This gate upgrades the existing Phase-2F/G nullable runtime + condition
translator from local semantic evidence to one self-contained native package.
It does not broaden the AST inventory, admit grammar, enable search, or claim
strategy/performance evidence.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
NATIVE_ROOT = ROOT / "tests/fixtures/phase2v_nullable_condition_native"
INDEX = NATIVE_ROOT / "native_evidence_manifest.json"

EXPECTED_NULLABLE = [
    "null", "null", "false", "true", "true", "true",
    "true", "true", "true", "true", "true", "true",
]
EXPECTED_TRIGGERS = [
    False, False, False, True, True, True,
    True, True, True, True, True, True,
]
REQUIRED_CONTEXTS = ("A1", "A2", "B1", "B2")


def test_nullable_condition_native_package_is_bound_and_narrow():
    """Require the package contract once the native campaign returns."""
    if not INDEX.is_file():
        pytest.skip("Phase-2V native package not yet returned from the review-gated campaign")
    manifest = json.loads(INDEX.read_text(encoding="utf-8"))

    assert manifest["scope"] == "frozen nullable runtime and condition translator only"
    assert manifest["grammar_admitted"] is False
    assert manifest["searchable"] is False
    assert manifest["phase3_authorized"] is False
    assert manifest["complete_phase2_gate"] is False
    assert manifest["contexts"] == list(REQUIRED_CONTEXTS)
    assert manifest["nullable_vector"] == EXPECTED_NULLABLE
    assert manifest["trigger_vector"] == EXPECTED_TRIGGERS
    assert manifest["native_parity"] == "PASS_EXACT"
    assert manifest["compile"]["error_count"] == 0
    assert manifest["compile"]["warning_count"] == 0

    for key in (
        "runtime_identity",
        "condition_translation_identity",
        "semantic_result_identity",
        "evidence_commit",
    ):
        assert manifest[key], f"missing durable binding: {key}"

    for context in REQUIRED_CONTEXTS:
        run = manifest["runs"][context]
        assert run["exit_code"] == 0
        assert run["completion_marker"] is True
        assert run["failure_marker"] is False
        assert run["reconciliation"] == "PASS_EXACT"
        assert run["nullable_vector"] == EXPECTED_NULLABLE
        assert run["trigger_vector"] == EXPECTED_TRIGGERS
        assert Path(ROOT / run["evidence_path"]).is_file()
