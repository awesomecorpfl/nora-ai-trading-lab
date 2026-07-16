from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = (ROOT / "phase-0a-h/windows/phase2-evidence-runner.ps1").read_text()


def test_runner_has_explicit_containment_package_mode():
    assert "package-containment" in RUNNER
    for token in ("ContainmentSourceRoot", "ContainmentSummaryPath", "ContainmentDestinationPath", "PublisherPath", "PublisherSha256"):
        assert token in RUNNER
    assert "-SourceRoot $ContainmentSourceRoot" in RUNNER
    assert "-SummaryPath $ContainmentSummaryPath" in RUNNER
    assert "-DestinationPath $ContainmentDestinationPath" in RUNNER
    assert "-ExpectedRunId $RunId" in RUNNER
    assert "Hash $PublisherPath" in RUNNER


def test_runner_package_mode_has_no_firewall_mutation():
    mode = RUNNER.split("'package-containment'", 1)[1].split("'record-import'", 1)[0]
    assert "New-NetFirewallRule" not in mode
    assert "Remove-NetFirewallRule" not in mode


def test_runner_has_repository_owned_abandoned_fixture_mode():
    assert "abandon-fixture" in RUNNER
    assert "ABANDONED_PRE_LAUNCH_NO_CONTAINMENT" in RUNNER
    assert "non_reusable=$true" in RUNNER
