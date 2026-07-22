"""Local preflight contract for the Phase-2V native runner."""
from __future__ import annotations

import json
from pathlib import Path

from scripts.phase2v_nullable_condition_native import build_plan

ROOT = Path(__file__).resolve().parents[1]


def test_phase2v_preflight_binds_frozen_sources_and_closed_boundaries():
    plan = build_plan(ROOT)
    runtime = json.loads(
        (ROOT / "tests/fixtures/phase2f_mql5_runtime/NoraPhase2RuntimeV1.manifest.json").read_text()
    )
    condition = json.loads(
        (ROOT / "tests/fixtures/phase2g_mql5_condition/NoraPhase2ConditionV1.manifest.json").read_text()
    )
    evidence = json.loads(
        (ROOT / "tests/fixtures/phase2g_translation_evidence.json").read_text()
    )

    assert plan["scope"] == "frozen nullable runtime and condition translator only"
    assert plan["runtime_identity"] == runtime["runtime_identity"]
    assert plan["condition_translation_identity"] == condition["translation_identity"]
    assert plan["canonical_ast_identity"] == evidence["canonical_ast_identity"]
    assert plan["nullable_vector"] == evidence["nullable_results"]
    assert plan["trigger_vector"] == evidence["triggers"]
    assert plan["contexts"] == ["A1", "A2", "B1", "B2"]
    assert plan["grammar_admitted"] is False
    assert plan["searchable"] is False
    assert plan["phase3_authorized"] is False
    assert plan["complete_phase2_gate"] is False
    assert plan["execution_authorized"] is False
