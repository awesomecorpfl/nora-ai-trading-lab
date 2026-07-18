import json
import tempfile
from pathlib import Path

import pytest

from lab.mql5gen.stateful import GenerationError, translate_stateful_condition


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "tests/fixtures/phase2f_mql5_runtime/NoraPhase2RuntimeV1.manifest.json"


def cross_document():
    return {"schema_version": 1, "root": {"kind": "cross", "direction": "above", "left": {"kind": "numeric_series", "ref": {"series": "close", "type": "numeric"}}, "right": {"kind": "numeric_series", "ref": {"series": "ema", "type": "numeric"}}}}


def slope_document():
    return {"schema_version": 1, "root": {"kind": "compare", "op": "gt", "left": {"type": "slope", "input": {"type": "series", "name": "close"}, "lookback": 1}, "right": {"kind": "number", "value": 0}}}


def test_stateful_translation_emits_previous_current_contract_deterministically():
    with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
        a, b = Path(first), Path(second)
        ast = a / "ast.json"
        ast.write_text(json.dumps(cross_document()))
        result_a = translate_stateful_condition(ast, RUNTIME, a)
        ast_b = b / "ast.json"
        ast_b.write_text(json.dumps(cross_document()))
        result_b = translate_stateful_condition(ast_b, RUNTIME, b)
        assert result_a["translation_identity"] == result_b["translation_identity"]
        assert (a / result_a["source_filename"]).read_bytes() == (b / result_b["source_filename"]).read_bytes()
        source = (a / result_a["source_filename"]).read_text()
        assert "previous" in source and "current" in source
        assert "NoraStatefulCrossAboveV1" in source
        assert result_a["stateful"] is True


def test_stateful_slope_translation_and_fail_closed_rejections():
    with tempfile.TemporaryDirectory() as directory:
        directory = Path(directory)
        ast = directory / "ast.json"
        ast.write_text(json.dumps(slope_document()))
        result = translate_stateful_condition(ast, RUNTIME, directory)
        source = (directory / result["source_filename"]).read_text()
        assert "NoraStatefulSlope1V1" in source
        assert result["series_bindings"][0]["original_series_name"] == "close"
        bad = directory / "bad.json"
        bad.write_text(json.dumps({"schema_version": 1, "root": {"kind": "cross", "direction": "above", "left": {"kind": "boolean_series", "ref": {"series": "flag", "type": "boolean"}}, "right": {"kind": "number", "value": 1}}}))
        with pytest.raises(GenerationError):
            translate_stateful_condition(bad, RUNTIME, directory / "bad")
