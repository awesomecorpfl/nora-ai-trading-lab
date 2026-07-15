from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = (ROOT / "phase-0a-h/windows/phase2-evidence-runner.ps1").read_text()
WORKER = (ROOT / "phase-0a-h/windows/execute-ten-strategy-packet.ps1").read_text()
ORCHESTRATOR = (ROOT / "scripts/phase2-ten-strategy-native-orchestrate").read_text()
CONTAINMENT = (ROOT / "phase-0a-h/windows/phase2-network-containment.ps1").read_text()
CACHE_INVENTORY = (ROOT / "phase-0a-h/windows/phase2-cache-inventory.ps1").read_text()
CACHE_SCOPE = (ROOT / "phase-0a-h/windows/resolve-phase2-mt5-server-scope.ps1").read_text()
CACHE_WORKER = (ROOT / "phase-0a-h/windows/execute-phase2-offline-cache-probe.ps1").read_text()
CACHE_PROBE = (ROOT / "phase-0a-h/windows/NoraPhase2OfflineCacheProbeV1.mq5").read_text()
DETACHED_CANARY = (ROOT / "phase-0a-h/windows/phase2-detached-canary.ps1").read_text()
FORENSIC_COLLECTOR = (ROOT / "phase-0a-h/windows/capture-phase2-run-forensics.ps1").read_text()


def test_runner_uses_the_persistent_evidence_root_and_sid_acl_contract():
    assert "C:\\NoraEvidence\\Phase2" in RUNNER
    assert "S-1-5-18" in RUNNER and "S-1-5-32-544" in RUNNER
    assert "S-1-5-11" in RUNNER and "S-1-5-32-545" in RUNNER
    assert "evidence root ACL inheritance enabled" in RUNNER
    assert "broad evidence write ACL" in RUNNER
    assert "runner_probe_create_finalize_read_hash_delete" in RUNNER


def test_detached_lifecycle_is_durable_and_ssh_independent():
    for state in ("prepared", "launched", "bootstrap-confirmed", "running", "completed", "failed", "abandoned", "packaging", "published", "accepted", "rejected"):
        assert state in RUNNER
    assert "Invoke-CimMethod -ClassName Win32_Process -MethodName Create" in RUNNER
    assert "nora.phase2_detached_bootstrap_v1" in RUNNER
    assert "Start-Process -FilePath powershell.exe" in RUNNER
    assert "ssh_disconnect_is_failure=$false" in RUNNER
    assert "ambiguous-incomplete" in RUNNER and "ambiguous-missing" in RUNNER
    assert "conflicting terminal_or_tester" in RUNNER
    assert "conflicting persistent campaign job" in RUNNER
    for binding in ("pid", "start_time_utc", "executable_path", "command_line", "run_identifier"):
        assert binding in RUNNER
    assert "$root=$EvidenceRoot" in WORKER
    assert ".running$','.complete'" in WORKER


def test_persistent_orchestrator_uses_only_the_repository_runner_commands():
    for mode in ("harden-acl", "recover-acl", "prepare", "launch", "status", "retrieve", "package-persistent", "record-import"):
        assert f"$mode == {mode}" in ORCHESTRATOR
    assert "phase2-evidence-runner.ps1" in ORCHESTRATOR
    assert "run is not durably completed" in ORCHESTRATOR
    assert "package not idempotent" in RUNNER
    assert "$mode == run" not in ORCHESTRATOR
    assert "jobs\\\\'+$RunId+'.linux-ingestion.json" in RUNNER
    assert "campaign-tool" in ORCHESTRATOR
    assert "bound runner hash mismatch" in ORCHESTRATOR
    assert "bound containment tool hash mismatch" in ORCHESTRATOR
    assert "tr -d '\\r\\n'" in ORCHESTRATOR


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
    assert "TrimStart([char]0xFEFF)" in RUNNER


def test_execution_policy_bypass_is_process_scoped_and_arguments_are_constrained():
    assert "-ExecutionPolicy Bypass -File" in ORCHESTRATOR
    assert "Set-ExecutionPolicy" not in ORCHESTRATOR
    assert "Set-ExecutionPolicy" not in RUNNER
    for guard in ("require_root", "require_run_id", "require_audit_id", "require_remote_path"):
        assert guard in ORCHESTRATOR


def test_offline_preflight_requires_containment_before_detached_probe_launch():
    for mode in ("cache-preflight-prepare", "cache-preflight-contain", "cache-preflight-launch", "cache-preflight-cleanup"):
        assert mode in RUNNER and mode in ORCHESTRATOR
    assert "-Action stage" in RUNNER and "-Action verify" in RUNNER
    assert "preflight_kind='offline_cache'" in RUNNER
    assert "foreach($key in $extra.Keys)" in RUNNER
    assert "LaunchDetached $p $worker $arguments $config 'offline_cache_probe'" in RUNNER


def test_bootstrap_and_universal_failure_records_precede_workload_execution():
    for token in ("bootstrap.json", "received_arguments", "configuration_sha256", "stdout_path", "stderr_path", "lifecycle-failure.json", "exception_type", "position_or_stack", "last_completed_lifecycle_step"):
        assert token in RUNNER
    assert "WriteJob $p 'bootstrap-confirmed'" in RUNNER
    assert "WriteJob $p 'failed'" in RUNNER
    assert "workload-failure-detail.json" in RUNNER


def test_real_canary_and_incomplete_classification_commands_are_repository_owned():
    for mode in ("canary-prepare", "canary-launch", "terminate-bound-canary", "finalize-canary", "classify-incomplete", "cleanup-incomplete"):
        assert mode in RUNNER and mode in ORCHESTRATOR
    for kind in ("success", "intentional-failure", "parameter-failure", "disconnect", "forced-termination"):
        assert kind in RUNNER
    assert "NORA_INTENTIONAL_DETACHED_CANARY_FAILURE" in DETACHED_CANARY
    assert "terminal64" not in DETACHED_CANARY.lower() and "metatester64" not in DETACHED_CANARY.lower()
    assert "nora.phase2_immutable_incomplete_run_v1" in RUNNER


def test_forensic_collector_is_copy_only_for_the_source_run_and_atomic():
    assert "nora.phase2_incomplete_run_forensic_capture_v1" in FORENSIC_COLLECTOR
    assert "source_inventory" in FORENSIC_COLLECTOR and "event_logs" in FORENSIC_COLLECTOR
    assert "Copy-Item -LiteralPath $Source" in FORENSIC_COLLECTOR
    assert "Move-Item -LiteralPath $partial -Destination $published" in FORENSIC_COLLECTOR
    assert "Remove-Item" not in FORENSIC_COLLECTOR


def test_containment_is_executable_scoped_durable_and_cleanup_is_explicit():
    for token in ("terminal64.exe", "metatester64.exe", "-Direction Outbound", "-Action Block", "-Profile Any", "Get-NetFirewallApplicationFilter", "Get-NetTCPConnection", "stale or incomplete containment transaction requires recovery"):
        assert token in CONTAINMENT
    assert "Remove-NetFirewallRule" in CONTAINMENT
    assert "function Get-NoraContainmentGroup" in CONTAINMENT
    assert "-Group (Group)" not in CONTAINMENT
    assert "-Group $firewallGroup" in CONTAINMENT
    assert "cleanup" in CONTAINMENT
    assert "sshd" not in CONTAINMENT.lower()
    assert "Set-ExecutionPolicy" not in CONTAINMENT


def test_containment_transaction_is_durable_reopen_verified_and_recoverable():
    for token in (
        "intent_prepared", "pre_state_captured", "rules_verified",
        "final_record_published", "final_record_reopened", "transaction_accepted",
        "RULES_PRESENT_RECORD_INCOMPLETE", "NO_RULES_TRANSACTION_FAILED",
        "FreshVerify", "transaction-accepted.json", "transaction-recovery.json",
        "after_first_rule", "after_all_rules_before_final",
    ):
        assert token in CONTAINMENT
    assert "-Action','verify" in CONTAINMENT
    assert "exit 1" in CONTAINMENT


def test_containment_group_binding_is_explicit_validated_and_recorded():
    for token in (
        "Get-NoraContainmentGroup -RunId $CampaignId",
        "[string]::IsNullOrWhiteSpace($firewallGroup)",
        "NoraPhase2Containment-[A-Za-z0-9]",
        "group=$firewallGroup",
        "-Group $firewallGroup",
    ):
        assert token in CONTAINMENT
    assert "function Group" not in CONTAINMENT
    assert "-Group (Group)" not in CONTAINMENT


def test_containment_executable_paths_are_normalized_before_collection_operations():
    for token in (
        "Normalize-NoraExecutablePaths",
        "[string[]]$normalizedExecutablePaths",
        "-WasBound $PSBoundParameters.ContainsKey('ExecutablePath')",
        "At least one executable path is required.",
        "duplicate containment executable",
        "reparse point containment executable path",
        "foreach($p in $normalizedExecutablePaths)",
    ):
        assert token in CONTAINMENT
    assert "$ExecutablePath.Count" not in CONTAINMENT
    assert "foreach($p in @($ExecutablePath))" not in CONTAINMENT


def test_stale_prepared_offline_job_is_reconciled_without_history_rewrite():
    assert "reconcile-no-containment" in RUNNER
    for token in (
        "ABANDONED_PRE_LAUNCH_NO_CONTAINMENT", "original-job.json",
        "nora.phase2_prelaunch_reconciliation_v1", "NO_CONTAINMENT_RULES_NO_DURABLE_RECORD",
        "reconciliation_original_job_sha256",
    ):
        assert token in RUNNER


def test_runner_replaces_durable_job_json_and_recovers_only_verified_containment():
    assert "[IO.File]::Replace" in RUNNER
    assert ".replace-backup." in RUNNER
    assert "Remove-Item -LiteralPath $backup -Force" in RUNNER
    assert "[IO.File]::Move" in RUNNER
    assert "containment_accepted_path" in RUNNER
    assert "containment_recovered_from_interrupted_job" in RUNNER
    assert "-Action status -CampaignId $RunId" in RUNNER


def test_cache_probe_is_nontrading_exact_range_and_rejects_history_changes():
    for token in ("2020.07.01", "2026.07.01", "PERIOD_M1", "CopyRates", "duplicate_timestamps", "nonmonotonic_timestamps", "TesterStop"):
        assert token in CACHE_PROBE
    for forbidden in ("OrderSend", "CTrade", "PositionOpen", "OrderClose"):
        assert forbidden not in CACHE_PROBE
    for token in ("CompareCache", "strict_no_history_mutation_subset", "successful_connection_observed", "blocked_attempt_observed", "offline-cache-preflight.json"):
        assert token in CACHE_WORKER
    assert "server_scope" in CACHE_INVENTORY and "empty_relevant_inventory" in CACHE_INVENTORY
    assert "server_binding_identity" in CACHE_WORKER and "renamed" in CACHE_WORKER


def test_server_scoped_inventory_is_template_bound_and_fails_closed_on_path_ambiguity():
    for token in ("origin.txt", "Server=", "ambiguous or missing tester server identity",
                  "ambiguous or missing server namespace", "unsafe tester server identity",
                  "server namespace escapes terminal Bases", "reparse point rejected",
                  "OrdinalIgnoreCase", "terminal_instance_id", "configuration_sha256"):
        assert token in CACHE_SCOPE
    for token in ("creation_utc", "acl", "object_type", "absolute_canonical_path",
                  "missing_directory", "filename_year_candidate_only", "relevant_file_count"):
        assert token in CACHE_INVENTORY
