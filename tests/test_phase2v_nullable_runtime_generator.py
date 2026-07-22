from __future__ import annotations

import json
import tempfile
from pathlib import Path

from lab.phase2v_nullable_runtime_native import generate

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/phase2f_mql5_nullable_semantics.json"


def test_nullable_runtime_tester_generation_is_frozen_and_exhaustive():
    with tempfile.TemporaryDirectory() as directory:
        result = generate(directory, FIXTURE)
        manifest = json.loads(Path(directory, result["source_filename"].replace(".mq5", ".manifest.json")).read_text())
        assert result["case_count"] == 44
        assert result["operations"] == ["not", "and", "or", "gt", "gte", "lt", "lte", "trigger"]
        assert manifest["semantic_fixture_sha256"] == __import__("hashlib").sha256(FIXTURE.read_bytes()).hexdigest()
        source = Path(directory, result["source_filename"]).read_text()
        for operation, count in {"NoraBoolNotV1": 3, "NoraBoolAndV1": 9, "NoraBoolOrV1": 9, "NoraCompareGtV1": 5, "NoraCompareGteV1": 5, "NoraCompareLtV1": 5, "NoraCompareLteV1": 5}.items():
            assert source.count(operation) == count
        assert source.count("NoraConditionTriggersV1") == 44


def test_nullable_runtime_tester_generation_refuses_existing_targets():
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory, "NoraPhase2ConditionTesterCanaryV1.mq5")
        target.write_text("operator-owned sentinel")
        try:
            generate(directory, FIXTURE)
        except ValueError as error:
            assert "must not already exist" in str(error)
        else:
            raise AssertionError("existing tester target was overwritten")
        assert target.read_text() == "operator-owned sentinel"
