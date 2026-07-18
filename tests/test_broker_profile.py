from pathlib import Path

import pytest

from lab.broker_profile import (
    SCHEMA,
    build_profile_boundary,
    load_canonical_profile,
    load_profile_boundary,
    load_strategyquantx_export,
    write_profile_boundary,
    write_strategyquantx_profile,
)
from lab.core import canon

FIXTURE = Path(__file__).parent / "fixtures" / "broker_profile" / "strategyquantx_export"


def _copy_fixture(destination):
    for source in FIXTURE.iterdir():
        (destination / source.name).write_bytes(source.read_bytes())


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
    assert len(eurusd["source_values"]["csv_header"]) == 59
    assert len(eurusd["source_values"]["csv_row"]) == 59
    assert eurusd["source_values"]["csv"]["point_value"] == "100000.0"
    assert eurusd["source_values"]["instrument_xml"]["tickStep"] == "0.00001"
    assert eurusd["session_name"] == "FX_Currency1_EURJPY_GBPJPY_USDJPY_EURUSD_GBPUSD"
    assert profile["profile_identity"]


def test_all_symbols_join_to_xml_and_sessions_and_identity_is_stable(tmp_path):
    profile = load_strategyquantx_export(FIXTURE)
    assert all(item["source_values"]["instrument_xml"] for item in profile["symbols"])
    assert all(item["session_name"] in profile["sessions"] for item in profile["symbols"])
    assert profile["profile_identity"] == load_strategyquantx_export(FIXTURE)["profile_identity"]
    for source in FIXTURE.iterdir():
        (tmp_path / source.name).write_bytes(source.read_bytes())
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text(csv_path.read_text(encoding="utf-8-sig").replace("1.14194", "1.14195", 1), encoding="utf-8")
    assert load_strategyquantx_export(tmp_path)["profile_identity"] != profile["profile_identity"]


def test_source_conflicts_are_warnings_not_silent_rewrites():
    profile = load_strategyquantx_export(FIXTURE)
    conflicts = {(item["symbol"], item["field"]) for item in profile["warnings"] if item["code"] == "SOURCE_VALUE_CONFLICT"}
    assert ("EURJPY", "point_value") in conflicts
    assert ("GBPJPY", "point_value") in conflicts


def test_conflict_matrix_includes_all_overlapping_fields(tmp_path):
    _copy_fixture(tmp_path)
    xml = tmp_path / "updated_instrument_information.xml"
    text = xml.read_text()
    for old, new in (("tickSize=\"0.010\"", "tickSize=\"0.011\""), ("tickStep=\"0.001\"", "tickStep=\"0.002\""), ("decimals=\"3\"", "decimals=\"4\""), ("defaultSpread=\"1.00\"", "defaultSpread=\"1.01\""), ("defaultSlippage=\"0.00\"", "defaultSlippage=\"0.01\""), ("orderSizeStep=\"0.01\"", "orderSizeStep=\"0.02\""), ("pointValue=\"616.374608\"", "pointValue=\"617.374608\""), ("long=&quot;1.80&quot;", "long=&quot;2.80&quot;"), ("type=&quot;points&quot;", "type=&quot;money&quot;"), ("type=&quot;SizeBased&quot;", "type=&quot;Other&quot;"), ("&gt;0.00&lt;/Param&gt;", "&gt;1.00&lt;/Param&gt;")):
        text = text.replace(old, new, 1)
    xml.write_text(text)
    fields = {item["field"] for item in load_strategyquantx_export(tmp_path)["warnings"] if item["code"] == "SOURCE_VALUE_CONFLICT"}
    assert {"pip_size", "trade_tick_size", "digits", "spread_pips", "slippage_pips", "volume_step", "point_value", "swap_long", "swap_type", "commission_type", "commission_value"} <= fields


def test_wrong_header_fails_closed(tmp_path):
    for source in FIXTURE.iterdir():
        (tmp_path / source.name).write_bytes(source.read_bytes())
    csv_path = tmp_path / "sample.csv"
    text = csv_path.read_text(encoding="utf-8-sig").replace("Instrument,Description", "Wrong,Description", 1)
    csv_path.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match="header"):
        load_strategyquantx_export(tmp_path)


def test_duplicate_csv_symbol_fails_closed(tmp_path):
    _copy_fixture(tmp_path)
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text(csv_path.read_text().replace("GBPUSD,", "EURUSD,", 1))
    with pytest.raises(ValueError, match="duplicate or empty symbol"):
        load_strategyquantx_export(tmp_path)


def test_duplicate_xml_records_and_set_mismatch_fail_closed(tmp_path):
    _copy_fixture(tmp_path)
    xml_path = tmp_path / "updated_instrument_information.xml"
    xml = xml_path.read_text()
    first = xml.split("\n", 2)[1]
    xml_path.write_text(xml.replace("</Instruments>", first + "\n</Instruments>", 1))
    with pytest.raises(ValueError, match="duplicate instrument"):
        load_strategyquantx_export(tmp_path)
    _copy_fixture(tmp_path)
    xml_path.write_text(xml_path.read_text().replace('instrument="GBPUSD"', 'instrument="MISSING"', 1))
    with pytest.raises(ValueError, match="CSV/XML"):
        load_strategyquantx_export(tmp_path)


def test_duplicate_session_name_fails_closed(tmp_path):
    _copy_fixture(tmp_path)
    path = tmp_path / "Sessions.xml"
    text = path.read_text()
    block = text[text.index("  <Session"):text.index("  </Session>") + len("  </Session>")]
    path.write_text(text.replace("</Sessions>", block + "\n</Sessions>", 1))
    with pytest.raises(ValueError, match="duplicate session"):
        load_strategyquantx_export(tmp_path)


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


def test_writer_publishes_reproducible_canonical_profile(tmp_path):
    output = tmp_path / "broker-profile.json"
    profile = write_strategyquantx_profile(FIXTURE, output)
    assert output.is_file()
    assert output.read_text() == canon(profile) + "\n"
    assert profile == load_strategyquantx_export(FIXTURE)


def test_canonical_profile_loader_rejects_identity_tampering(tmp_path):
    output = tmp_path / "broker-profile.json"
    expected = write_strategyquantx_profile(FIXTURE, output)
    assert load_canonical_profile(output) == expected
    tampered = dict(expected)
    tampered["profile_identity"] = "0" * 64
    output.write_text(canon(tampered) + "\n")
    with pytest.raises(ValueError, match="profile identity"):
        load_canonical_profile(output)


def test_representative_instrument_families_are_derived_explicitly():
    profile = load_strategyquantx_export(FIXTURE)
    families = {item["symbol"]: item["identity"]["instrument_family"] for item in profile["symbols"]}
    assert {symbol for symbol, family in families.items() if family == "forex"} == {"EURUSD", "GBPUSD", "EURJPY", "GBPJPY", "USDJPY"}
    assert {symbol for symbol, family in families.items() if family == "indices"} == {"GDAXI", "NDX", "SP500"}
    assert families["IVE"] == "equity_etf"
    assert families["XAUUSD"] == "metals_commodities"


def test_representative_family_contracts_keep_observed_type_differences():
    profile = load_strategyquantx_export(FIXTURE)
    by_symbol = {item["symbol"]: item for item in profile["symbols"]}
    eurusd = by_symbol["EURUSD"]
    eurjpy = by_symbol["EURJPY"]
    gdaxi = by_symbol["GDAXI"]
    ive = by_symbol["IVE"]
    xauusd = by_symbol["XAUUSD"]

    assert eurusd["price"]["digits"] == 5
    assert eurusd["price"]["pip_size_observed"] == 0.0001
    assert eurusd["price"]["trade_tick_size_observed"] == 0.00001
    assert eurjpy["price"]["digits"] == 3
    assert eurjpy["price"]["pip_size_observed"] == 0.01
    assert eurjpy["price"]["trade_tick_size_observed"] == 0.001
    assert gdaxi["contract"]["contract_size_observed"] == 10.0
    assert gdaxi["price"]["digits"] == 1
    assert ive["contract"]["volume_min_observed"] == 1.0
    assert ive["contract"]["volume_step_observed"] == 1.0
    assert xauusd["contract"]["contract_size_observed"] == 100.0
    assert xauusd["price"]["trade_tick_size_observed"] == 0.01


def test_profile_boundary_keeps_observations_separate_from_unbound_policy():
    profile = load_strategyquantx_export(FIXTURE)
    boundary = build_profile_boundary(profile)
    assert boundary["schema_version"] == "nora.broker_profile_boundary_v1"
    assert boundary["source_profile_identity"] == profile["profile_identity"]
    assert boundary["observed_profile"] == profile
    assert boundary["policy"] == {
        "status": "unbound",
        "bindings": {},
        "unbound_fields": [
            "spread_model",
            "commission_model",
            "slippage_model",
            "swap_model",
            "account_currency",
            "sizing",
            "leverage_margin",
            "session_policy",
        ],
    }
    tampered = dict(profile)
    tampered["profile_identity"] = "0" * 64
    with pytest.raises(ValueError, match="profile identity"):
        build_profile_boundary(tampered)


def test_profile_boundary_artifact_round_trip_rejects_policy_tampering(tmp_path):
    profile = load_strategyquantx_export(FIXTURE)
    output = tmp_path / "profile-boundary.json"
    expected = write_profile_boundary(profile, output)
    assert expected == build_profile_boundary(profile)
    assert load_profile_boundary(output) == expected
    tampered = dict(expected)
    tampered["policy"] = dict(expected["policy"])
    tampered["policy"]["bindings"] = {"spread_model": {"default": 1.0}}
    output.write_text(canon(tampered) + "\n")
    with pytest.raises(ValueError, match="policy boundary"):
        load_profile_boundary(output)
