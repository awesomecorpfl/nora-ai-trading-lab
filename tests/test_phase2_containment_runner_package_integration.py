from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = (ROOT / "phase-0a-h/windows/phase2-evidence-runner.ps1").read_text()
CONTAINMENT = (ROOT / "phase-0a-h/windows/phase2-network-containment.ps1").read_text()
DEPLOY = (ROOT / "scripts/phase2-deploy-windows-binary").read_text()


def test_runner_has_explicit_containment_package_mode():
    assert "package-containment" in RUNNER
    for token in ("ContainmentSourceRoot", "ContainmentSummaryPath", "ContainmentDestinationPath", "PublisherPath", "PublisherSha256"):
        assert token in RUNNER
    assert "direct containment package publication is forbidden" in RUNNER


def test_runner_inventory_binds_the_actual_intent_record_path():
    assert "intent='.intent.json'" in RUNNER
    assert "intent='intent.json'" not in RUNNER
    assert "capture-containment-command" in RUNNER
    assert "-SourceRoot $captureRoot" in RUNNER
    assert "-SummaryPath $summarySidecar" in RUNNER
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
    assert "$summarySidecar=$captureRoot+'.summary.json'" in mode
    assert "-SummaryPath $summarySidecar" in mode
    assert "Move-Item -LiteralPath $partial -Destination $captureRoot" in mode
    assert "$PublisherPath -SourceRoot $captureRoot" in mode
    for token in ("FirewallBindingPath","FirewallBindingSha256","nora.phase2_operation_firewall_binding_v1","firewall binding verdict failure","firewall_preservation=$firewallBinding"):
        assert token in RUNNER
    for token in ("FirewallCaptureToolPath","FirewallCaptureToolSha256","CaptureCompleteFirewall","firewall_inventory_pre.json","firewall_inventory_post.json","FirewallVerdict","capture_order=@('pre','operation','post')"):
        assert token in RUNNER


def test_runner_binds_multiple_executables_as_one_array_argument():
    mode = RUNNER.split("'capture-containment-command'", 1)[1].split("'package-containment'", 1)[0]
    assert "$arguments+=@('-ExecutablePath',($ContainmentExecutablePath -join ','))" in mode


def test_containment_decodes_runner_array_token_before_path_binding():
    assert "if($normalizedExecutablePaths.Count -eq 1 -and $normalizedExecutablePaths[0].Contains(','))" in CONTAINMENT


def test_runner_has_repository_owned_abandoned_fixture_mode():
    assert "abandon-fixture" in RUNNER
    assert "abandon-fixture-cleanup" in RUNNER
    assert "ABANDONED_PRE_LAUNCH_NO_CONTAINMENT" in RUNNER
    assert "non_reusable=$true" in RUNNER
    assert "created_or_modified_durable_record=$false" in RUNNER
    assert "created_or_modified_firewall_rule=$false" in RUNNER
    assert "'runner-operation'" in RUNNER
    assert "missing structured runner operation mode" in RUNNER
    assert "operationTool=$PSCommandPath" in RUNNER


def test_runner_has_read_only_firewall_qualification_mode():
    branch = RUNNER.split("'firewall-readonly' {", 1)[1].split("\n }", 1)[0]
    assert "Get-NetFirewallProfile -PolicyStore ActiveStore" in branch
    assert "Get-NetFirewallRule -PolicyStore ActiveStore" in branch
    assert "firewall_mutation_requested=$false" in branch
    for cmdlet in ("New-NetFirewallRule", "Set-NetFirewallRule", "Remove-NetFirewallRule", "Disable-NetFirewallRule", "Enable-NetFirewallRule"):
        assert cmdlet not in branch


def test_deployment_helper_is_stdin_isolated_and_hash_addressed():
    assert "NORA_SSH_CONFIG must name the established explicit SSH configuration" in DEPLOY
    assert 'ssh_cmd=(ssh -F "$NORA_SSH_CONFIG" -n nora-win10)' in DEPLOY
    assert '"${ssh_cmd[@]}"' in DEPLOY
    assert "ssh -n nora-win10" not in DEPLOY
    assert "AppendAllText" in DEPLOY
    assert "-EncodedCommand" in DEPLOY
    assert "iconv -f UTF-8 -t UTF-16LE" in DEPLOY
    assert "base64 -w 1024" in DEPLOY
    assert "chunk_count" in DEPLOY
    assert "Get-FileHash -Algorithm SHA256" in DEPLOY
    assert "Move-Item -LiteralPath \\$decoded -Destination \\$dest" in DEPLOY
    assert "-Path \\$parent" in DEPLOY
    assert "LiteralPath \\$dest" in DEPLOY
    assert "remote_dest != *'$'*" in DEPLOY
