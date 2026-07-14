from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=(ROOT/'phase-0a-h/windows/execute-ten-strategy-packet.ps1').read_text()

def test_packet_launcher_inherits_configured_template_and_rejects_stale_artifacts():
    assert "backtest_run.ini" in SCRIPT
    assert "Environment','Login','Server" in SCRIPT
    assert "if(Test-Path $commonCsv){Remove-Item $commonCsv -Force}" in SCRIPT
    assert "missing fresh CSV" in SCRIPT and "launch_or_completion_contract" in SCRIPT

def test_packet_launcher_binds_current_packet_chain_and_requires_agent_ea_fixture_and_marker():
    # Fresh corrected compilation must not be blocked by stale historical IDs.
    assert "$batch.execution_packet_identity-ne$packet.execution_packet_identity" in SCRIPT
    assert "packet.target_identifier-ne$target" in SCRIPT
    for token in ('tester_agent_started','ea_started','fixture_consumed','completion_marker_present','failure_marker_present'):
        assert token in SCRIPT
