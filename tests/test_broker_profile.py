from pathlib import Path

import pytest

from lab.broker_profile import SCHEMA, load_strategyquantx_export

FIXTURE = Path(__file__).parent / "fixtures" / "broker_profile" / "strategyquantx_export"


def test_strategyquantx_export_normalizes_all_symbols_and_preserves_sources():
    profile = load_strategyquantx_export(FIXTURE)
    assert profile["schema_version"] == SCHEMA
    assert len(profile["symbols"]) == 10
    assert len(profile["sessions"]) == 5
    assert len(profile["provenance"]["files"]) == 3
    assert profile["provenance"]["raw_preserved"] is True
    eurusd = next(item for item in profile["symbols"] if item["symbol"] == "EURUSD")
    assert eurusd["price"]["digits"] == 5
    assert eurusd["price"]["point_size_derived"] == 0.00001
    assert eurusd["contract"]["volume_min_observed"] == 0.01
    assert eurusd["costs"]["spread_pips_observed"] == 0.4
    assert eurusd["source_values"]["csv"]["point_value"] == "100000.0"
    assert eurusd["source_values"]["instrument_xml"]["tickStep"] == "0.00001"
    assert eurusd["session_name"] == "FX_Currency1_EURJPY_GBPJPY_USDJPY_EURUSD_GBPUSD"
    assert profile["profile_identity"]


def test_source_conflicts_are_warnings_not_silent_rewrites():
    profile = load_strategyquantx_export(FIXTURE)
    conflicts = {(item["symbol"], item["field"]) for item in profile["warnings"] if item["code"] == "SOURCE_VALUE_CONFLICT"}
    assert ("EURJPY", "point_value") in conflicts
    assert ("GBPJPY", "point_value") in conflicts


def test_rejects_unsafe_xml_declarations(tmp_path):
    for source in FIXTURE.iterdir():
        (tmp_path / source.name).write_bytes(source.read_bytes())
    sessions = tmp_path / "Sessions.xml"
    sessions.write_bytes(b"<!DOCTYPE Sessions SYSTEM 'external'>" + sessions.read_bytes())
    with pytest.raises(ValueError, match="unsafe XML"):
        load_strategyquantx_export(tmp_path)


def test_missing_or_ragged_source_fails_closed(tmp_path):
    for source in FIXTURE.iterdir():
        (tmp_path / source.name).write_bytes(source.read_bytes())
    lines = (tmp_path / "sample.csv").read_text(encoding="utf-8-sig").splitlines()
    (tmp_path / "sample.csv").write_text("\n".join(lines[:-1] + [lines[-1] + ",extra"]) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="ragged"):
        load_strategyquantx_export(tmp_path)
