import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "docs/evidence/phase2/frt1r2-operator-preparation/20260717T192223Z/packet.json"
HELPER = ROOT / "phase-0a-h/windows/phase2-operator-state.ps1"
QUALIFICATION_SCRIPT = ROOT / "phase-0a-h/windows/phase2-frt1r2-operator-qualification.ps1"
RUNNER = ROOT / "phase-0a-h/windows/phase2-evidence-runner.ps1"
RESTORATION_SCRIPT = ROOT / "phase-0a-h/windows/phase2-tester-rule-restoration.ps1"
HARNESS = ROOT / "tests/windows/phase2_operator_state_harness.ps1"
REPAIR_HARNESS = ROOT / "tests/windows/phase2_fail_closed_repair_harness.ps1"
REPAIR_EVIDENCE = ROOT / "docs/evidence/phase2/pi0-outgoing-review-repair/20260718T004745Z"
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


def test_qualification_rejects_every_existing_identity_artifact_before_creating_root():
    source = QUALIFICATION_SCRIPT.read_text()
    collision_guard = "Get-ChildItem -LiteralPath $EvidenceBase -Force -ErrorAction Stop"
    rejection = "NORA_QUALIFICATION_IDENTITY_REUSE_REJECTED"
    create_root = "New-Item -ItemType Directory -Path $evidence -ErrorAction Stop"
    assert collision_guard in source
    assert "('*'+$QualificationId+'*')" in source
    assert rejection in source
    assert create_root in source
    assert source.index(collision_guard) < source.index(rejection) < source.index(create_root)
    assert "New-Item -ItemType Directory -Path $evidence -Force" not in source


def test_repository_job_reader_rejects_every_partial_or_orphan_reconciliation_entry():
    source = HELPER.read_text()
    assert "Get-ChildItem -LiteralPath $reconRoot -Force -ErrorAction Stop" in source
    assert "reconciliation partial or orphan entry" in source
    assert "-notmatch '^[A-Za-z0-9][A-Za-z0-9._-]{2,127}\\.published$'" in source


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
    assert powershell is not None
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
    assert '"partial_reconciliation":"FAIL_AS_EXPECTED"' in result.stdout


def test_windows_powershell_fail_closed_repair_harness():
    powershell = shutil.which("powershell") or shutil.which("pwsh")
    if not powershell:
        pytest.skip("PowerShell 5.1 unavailable on this Linux host")
    assert powershell is not None
    result = subprocess.run(
        [
            powershell, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
            "-File", str(REPAIR_HARNESS),
            "-QualificationScript", str(QUALIFICATION_SCRIPT),
            "-RunnerScript", str(RUNNER),
            "-OperatorStateHelper", str(HELPER),
            "-RestorationScript", str(RESTORATION_SCRIPT),
        ],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert '"verdict":"PASS"' in result.stdout
    assert '"burned_qualification_identity":"FAIL_AS_EXPECTED"' in result.stdout
    assert '"competing_prepared_job":"FAIL_AS_EXPECTED"' in result.stdout
    assert '"legacy_competing_prepared_job":"FAIL_AS_EXPECTED"' in result.stdout
    assert '"unrelated_firewall_digest":"PASS"' in result.stdout
    assert '"restoration_self_hash":"FAIL_AS_EXPECTED"' in result.stdout
    assert '"firewall_mutation_invoked":false' in result.stdout
    assert '"mt5_invoked":false' in result.stdout


def test_pi0_review_repair_evidence_is_hash_bound_and_noncredit():
    manifest = json.loads((REPAIR_EVIDENCE / "manifest.json").read_text())
    assert manifest["repository_commit"] == "f2531030b6e2c64ddca8b8d2f5a6d2e6a90df997"
    assert manifest["classification"] == "REPAIR_VALIDATED_NON_ACCEPTANCE"
    assert manifest["acceptance_credit_granted"] is False
    for artifact in manifest["artifacts"]:
        path = ROOT / artifact["path"]
        data = path.read_bytes()
        assert len(data) == artifact["size"]
        assert hashlib.sha256(data).hexdigest() == artifact["sha256"]
    for binding in manifest["implementation_bindings"]:
        data = subprocess.check_output(
            ["git", "show", f'{manifest["repository_commit"]}:{binding["path"]}'],
            cwd=ROOT,
        )
        assert hashlib.sha256(data).hexdigest() == binding["sha256"]
    for binding in manifest["external_historical_bindings"]:
        assert hashlib.sha256((ROOT / binding["path"]).read_bytes()).hexdigest() == binding["sha256"]
    supersession = json.loads((REPAIR_EVIDENCE / "supersession.json").read_text())
    assert supersession["superseded_packet"]["classification"] == "NON_CREDIT_SUPERSEDED_PREPARATION"
    assert supersession["replacement_live_packet"] is None
    assert supersession["may_execute_superseded_packet"] is False
    diagnostic = json.loads((REPAIR_EVIDENCE / "diagnostic-classification.json").read_text())
    assert diagnostic["classification"] == "NON_CREDIT_UNSEALED_DIAGNOSTIC"
    assert diagnostic["acceptance_credit_granted"] is False
