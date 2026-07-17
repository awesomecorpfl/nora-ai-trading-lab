import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "docs/evidence/phase2/frt1r2-operator-preparation/20260717T192223Z/packet.json"
HELPER = ROOT / "phase-0a-h/windows/phase2-operator-state.ps1"
HARNESS = ROOT / "tests/windows/phase2_operator_state_harness.ps1"
QUALIFICATION_ID = "frt1r2-live-20260717T192223Z"


def packet():
    return json.loads(PACKET.read_text())


def test_packet_is_fail_closed_and_uses_repository_state_reader():
    value = packet()
    pre = value["preconditions_command"]
    post = value["postflight_verification_command"]
    for body in (pre, post):
        assert "phase2-operator-state.ps1" in body
        assert "active_job_count" in body
        assert "pending_job_count" in body
        assert "unresolved_prepared_job_count" in body
        assert "scheduled_nora_task_count" in body
        assert "verdict='PASS'" in body
        assert "Get-ChildItem -LiteralPath (Join-Path $root 'jobs')" not in body
        assert "Get-ScheduledTask" not in body
    assert "$nora.Count -ne 0" in pre
    assert "$proc.Count -ne 0" in pre
    assert "-or $state.active_job_count -ne 0" in pre
    assert "-or $state.pending_job_count -ne 0" in pre
    assert "-or $state.unresolved_prepared_job_count -ne 0" in pre
    assert "-or $state.scheduled_nora_task_count -ne 0" in pre
    assert "profiles must be exactly three and all enabled" in pre
    assert "tester rule must exist exactly once" in pre
    assert "tester rule must be disabled" in pre
    assert "qualification-specific containment state unresolved" in post
    assert "unrelated firewall mismatch" not in post or "unrelated_firewall_unchanged" in post


def test_repository_job_reader_contains_reconciliation_fail_closed_contract():
    source = HELPER.read_text()
    for token in (
        "Read-ReconciledJobFile", "legacy job contradictory field:",
        "legacy job key/value count mismatch", "nora.phase2_prelaunch_reconciliation_v1",
        "ABANDONED_PRE_LAUNCH_NO_CONTAINMENT", "reconciliation original job mismatch",
        "Read-ReconciliationBinding", "original-job.json", "reconciliation original job missing",
        "reconciliation original job size mismatch", "reconciliation has no source job", "published reconciliation incomplete",
        "current_job_changed_after_reconciliation", "ReadAllBytes",
        "unknown job state", "unresolved_prepared_job_count",
    ):
        assert token in source


def test_live_and_cleanup_commands_remain_bound_to_existing_id():
    value = packet()
    assert QUALIFICATION_ID in value["live_qualification_command"]
    assert QUALIFICATION_ID in value["emergency_cleanup_command"]
    assert "192223Z" in value["live_qualification_command"]
    assert "192223Z" in value["emergency_cleanup_command"]
    assert "185409Z" not in value["live_qualification_command"]
    assert "185409Z" not in value["emergency_cleanup_command"]


@pytest.mark.parametrize(
    "required_text",
    [
        "nora_rule_count",
        "terminal_tester_process_count",
        "active_job_count",
        "pending_job_count",
        "unresolved_prepared_job_count",
        "scheduled_nora_task_count",
        "tester_rule_enabled",
        "containment_state='resolved'",
        "unrelated_firewall_unchanged",
    ],
)
def test_packet_reports_each_safety_dimension(required_text):
    value = packet()
    assert required_text in value["preconditions_command"] or required_text in value["postflight_verification_command"]


def test_windows_powershell_job_reconciliation_harness():
    powershell = shutil.which("powershell") or shutil.which("pwsh")
    if not powershell:
        pytest.skip("PowerShell 5.1 unavailable on this Linux host")
    result = subprocess.run(
        [powershell, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(HARNESS), "-HelperPath", str(HELPER)],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert '"verdict":"PASS"' in result.stdout
    assert '"safe_reconciled":"PASS"' in result.stdout
    assert '"mutation_after_publication":"PASS"' in result.stdout
    assert '"legacy_nested_keys_values":"PASS"' in result.stdout
    assert '"unresolved_prepared":"FAIL_AS_EXPECTED"' in result.stdout
    assert '"contradictory_reconciliation":"FAIL_AS_EXPECTED"' in result.stdout
