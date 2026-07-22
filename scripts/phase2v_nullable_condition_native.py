#!/usr/bin/env python3
"""Phase-2V nullable runtime/condition native-campaign preflight.

This command builds a deterministic review plan from the frozen Phase-2F/G
artifacts. It does not launch Windows, mutate firewall state, publish evidence,
or claim native parity. The plan is the input to the human review gate before
any native campaign is authorized.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

RUNTIME_MANIFEST = Path("tests/fixtures/phase2f_mql5_runtime/NoraPhase2RuntimeV1.manifest.json")
RUNTIME_SOURCE = Path("tests/fixtures/phase2f_mql5_runtime/NoraPhase2RuntimeV1.mqh")
CONDITION_MANIFEST = Path("tests/fixtures/phase2g_mql5_condition/NoraPhase2ConditionV1.manifest.json")
CONDITION_SOURCE = Path("tests/fixtures/phase2g_mql5_condition/NoraPhase2ConditionV1.mqh")
SEMANTIC_FIXTURE = Path("tests/fixtures/phase2f_mql5_nullable_semantics.json")
TRANSLATION_EVIDENCE = Path("tests/fixtures/phase2g_translation_evidence.json")
AST_FIXTURE = Path("engine/labengine/tests/fixtures/phase2_ast_evaluate_task.json")
COMPILE_HELPER = Path("phase-0a-h/windows/compile-condition-tester-canary-durable.ps1")
EXECUTE_HELPER = Path("phase-0a-h/windows/execute-condition-tester-canary-durable.ps1")

CONTEXTS = ["A1", "A2", "B1", "B2"]
SYMBOLS = {"A1": "GDAXI/M1", "A2": "GDAXI/M1", "B1": "AUDCAD/M1", "B2": "AUDCAD/M1"}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(root: Path, relative: Path) -> dict:
    path = root / relative
    if not path.is_file():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8-sig"))


def build_plan(root: Path | str) -> dict:
    """Verify frozen inputs and return a closed, non-executing campaign plan."""
    root = Path(root)
    runtime = _load(root, RUNTIME_MANIFEST)
    condition = _load(root, CONDITION_MANIFEST)
    semantic = _load(root, SEMANTIC_FIXTURE)
    evidence = _load(root, TRANSLATION_EVIDENCE)
    ast = _load(root, AST_FIXTURE)

    runtime_source_sha = _sha256(root / RUNTIME_SOURCE)
    condition_source_sha = _sha256(root / CONDITION_SOURCE)
    if runtime_source_sha != runtime["source_sha256"]:
        raise ValueError("Phase-2F runtime source hash diverges from its frozen manifest")
    if condition_source_sha != condition["source_sha256"]:
        raise ValueError("Phase-2G condition source hash diverges from its frozen manifest")
    if evidence["canonical_ast_identity"] != condition["canonical_ast_identity"]:
        raise ValueError("Phase-2G evidence AST identity diverges from condition manifest")
    if ast["ast"]["schema_version"] != 1:
        raise ValueError("unexpected AST fixture schema version")

    return {
        "schema_version": "nora.phase2v.native_preflight_v1",
        "scope": "frozen nullable runtime and condition translator only",
        "runtime_source": str(RUNTIME_SOURCE),
        "condition_source": str(CONDITION_SOURCE),
        "semantic_fixture": str(SEMANTIC_FIXTURE),
        "translation_evidence": str(TRANSLATION_EVIDENCE),
        "runtime_identity": runtime["runtime_identity"],
        "runtime_source_sha256": runtime_source_sha,
        "condition_translation_identity": condition["translation_identity"],
        "condition_source_sha256": condition_source_sha,
        "canonical_ast_identity": evidence["canonical_ast_identity"],
        "nullable_vector": evidence["nullable_results"],
        "trigger_vector": evidence["triggers"],
        "contexts": CONTEXTS,
        "symbols": SYMBOLS,
        "transport": {
            "compile_helper": str(COMPILE_HELPER),
            "execute_helper": str(EXECUTE_HELPER),
            "execution_mode": "review_required",
            "broker_access": "required_for_mt5_tester_core",
            "firewall_mutation": False,
        },
        "grammar_admitted": False,
        "searchable": False,
        "phase3_authorized": False,
        "complete_phase2_gate": False,
        "execution_authorized": False,
        "native_parity": "NOT_RUN",
    }


def write_plan(root: Path | str, output: Path | str) -> dict:
    plan = build_plan(root)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".partial")
    temporary.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(output)
    return plan


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    plan = write_plan(args.root, args.output)
    print(json.dumps({"status": "preflight_ready", "output": str(args.output), "native_parity": plan["native_parity"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
