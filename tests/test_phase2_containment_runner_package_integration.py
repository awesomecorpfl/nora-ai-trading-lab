from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = (ROOT / "phase-0a-h/windows/phase2-evidence-runner.ps1").read_text()
DEPLOY = (ROOT / "scripts/phase2-deploy-windows-binary").read_text()


def test_runner_has_explicit_containment_package_mode():
    assert "package-containment" in RUNNER
    for token in ("ContainmentSourceRoot", "ContainmentSummaryPath", "ContainmentDestinationPath", "PublisherPath", "PublisherSha256"):
        assert token in RUNNER
    assert "direct containment package publication is forbidden" in RUNNER
    assert "capture-containment-command" in RUNNER
    assert "-SourceRoot $captureRoot" in RUNNER
    assert "-SummaryPath (Join-Path $captureRoot 'summary.json')" in RUNNER
    assert "-ExpectedRunId $RunId" in RUNNER
    assert "Hash $PublisherPath" in RUNNER


def test_runner_package_mode_has_no_firewall_mutation():
    mode = RUNNER.split("'package-containment'", 1)[1].split("'record-import'", 1)[0]
    assert "New-NetFirewallRule" not in mode
    assert "Remove-NetFirewallRule" not in mode


def test_runner_owned_capture_executes_and_binds_real_command_artifacts():
    mode = RUNNER.split("'capture-containment-command'", 1)[1].split("'package-containment'", 1)[0]
    for token in (
        "CaptureContainmentProcess", "stdout.txt", "stderr.txt", "pre_state.json",
        "post_state.json", "firewall_pre.json", "firewall_post.json", "processes.json",
        "capture_provenance", "containment capture identity already exists",
    ):
        assert token in mode
    assert "Move-Item -LiteralPath $partial -Destination $captureRoot" in mode
    assert "$PublisherPath -SourceRoot $captureRoot" in mode


def test_runner_has_repository_owned_abandoned_fixture_mode():
    assert "abandon-fixture" in RUNNER
    assert "ABANDONED_PRE_LAUNCH_NO_CONTAINMENT" in RUNNER
    assert "non_reusable=$true" in RUNNER


def test_deployment_helper_is_stdin_isolated_and_hash_addressed():
    assert "ssh -n nora-win10" in DEPLOY
    assert "AppendAllText" in DEPLOY
    assert "Text.Encoding]::ASCII" in DEPLOY
    assert "base64 -w 1024" in DEPLOY
    assert "chunk_count" in DEPLOY
    assert "Get-FileHash -Algorithm SHA256" in DEPLOY
    assert "Move-Item -LiteralPath \\$decoded -Destination \\$dest" in DEPLOY
    assert "-Path \\$parent" in DEPLOY
    assert "LiteralPath \\$dest" in DEPLOY
    assert "remote_dest != *'$'*" in DEPLOY
