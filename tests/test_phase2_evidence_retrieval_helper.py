from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "phase-0a-h/windows/read-phase2-evidence-file.ps1"


def test_evidence_reader_has_an_explicit_windows_path_boundary():
    source = HELPER.read_text(encoding="utf-8")
    for required in (
        "[System.IO.Path]::GetFullPath",
        "[System.StringComparison]::OrdinalIgnoreCase",
        "literal_path.outside_root",
        "literal_path.drive_mismatch",
        "$ParameterName.alternate_data_stream",
        "$ParameterName.traversal",
        "component.reparse_point",
        "-LiteralPath",
        "OpenStandardOutput",
    ):
        assert required in source
    assert "Invoke-Expression" not in source
    assert "StartsWith($root," not in source


def test_evidence_reader_keeps_production_root_fixed_and_test_mode_bounded():
    source = HELPER.read_text(encoding="utf-8")
    assert "$evidenceRoot = 'C:\\NoraEvidence\\Phase2'" in source
    assert "C:\\NoraTransportFixture'" in source
    assert "synthetic_root.not_permitted" in source
    assert "synthetic_root.without_test_mode" in source


def test_evidence_reader_streams_in_bounded_chunks_not_a_whole_file_buffer():
    source = HELPER.read_text(encoding="utf-8")
    assert "New-Object byte[] 65536" in source
    assert "[IO.File]::ReadAllBytes" not in source
