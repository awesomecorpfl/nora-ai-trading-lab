from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = (ROOT / "phase-0a-h/windows/phase2-evidence-runner.ps1").read_text()
WORKER = (ROOT / "phase-0a-h/windows/execute-ten-strategy-packet.ps1").read_text()
ORCHESTRATOR = (ROOT / "scripts/phase2-ten-strategy-native-orchestrate").read_text()


def test_runner_uses_the_persistent_evidence_root_and_sid_acl_contract():
    assert "C:\\NoraEvidence\\Phase2" in RUNNER
    assert "S-1-5-18" in RUNNER and "S-1-5-32-544" in RUNNER
    assert "S-1-5-11" in RUNNER and "S-1-5-32-545" in RUNNER
    assert "evidence root ACL inheritance enabled" in RUNNER
    assert "broad evidence write ACL" in RUNNER
    assert "runner_probe_create_finalize_read_hash_delete" in RUNNER


def test_detached_lifecycle_is_durable_and_ssh_independent():
    for state in ("prepared", "launched", "terminal-completed", "packaging", "published", "accepted", "rejected"):
        assert state in RUNNER
    assert "Start-Process -FilePath powershell.exe" in RUNNER
    assert "ssh_disconnect_is_failure=$false" in RUNNER
    assert "ambiguous-incomplete" in RUNNER and "ambiguous-missing" in RUNNER
    assert "conflicting terminal_or_tester" in RUNNER
    assert "conflicting persistent campaign job" in RUNNER
    assert "$root=$EvidenceRoot" in WORKER
    assert ".running$','.complete'" in WORKER


def test_persistent_orchestrator_uses_only_the_repository_runner_commands():
    for mode in ("harden-acl", "recover-acl", "prepare", "launch", "status", "retrieve", "package-persistent", "record-import"):
        assert f"$mode == {mode}" in ORCHESTRATOR
    assert "phase2-evidence-runner.ps1" in ORCHESTRATOR
    assert "run is not durably terminal-completed" in ORCHESTRATOR
    assert "package not idempotent" in RUNNER
    assert "$mode == run" not in ORCHESTRATOR
    assert "jobs\\\\'+$RunId+'.linux-ingestion.json" in RUNNER


def test_acl_recovery_is_hash_bound_atomic_and_fails_closed():
    assert "'recover-acl'" in RUNNER
    assert "untrusted ACL recovery tool" in RUNNER
    assert "recovery-failed." in RUNNER
    assert "partial ACL recovery publication" in RUNNER
    assert "post_baseline_administrative_files" in RUNNER
    assert "unexpected_post_baseline_files" in RUNNER
    assert "Move-Item -LiteralPath $partial -Destination $recovery" in RUNNER
    assert "recovery-tool" in ORCHESTRATOR
    assert "ExpectedToolSha256" in ORCHESTRATOR
    assert "TrimEnd(':','\\')" in RUNNER
    assert "TrimStart('\\').Replace('\\','/')" in RUNNER


def test_execution_policy_bypass_is_process_scoped_and_arguments_are_constrained():
    assert "-ExecutionPolicy Bypass -File" in ORCHESTRATOR
    assert "Set-ExecutionPolicy" not in ORCHESTRATOR
    assert "Set-ExecutionPolicy" not in RUNNER
    for guard in ("require_root", "require_run_id", "require_audit_id", "require_remote_path"):
        assert guard in ORCHESTRATOR
