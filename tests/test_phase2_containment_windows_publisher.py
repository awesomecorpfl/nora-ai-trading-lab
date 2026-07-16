from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "phase-0a-h/windows/build-containment-evidence-package.ps1").read_text()


def test_windows_publisher_matches_contract():
    for token in (
        "nora.phase2_containment_atomic_evidence_v1", "ZipArchive", "NoCompression",
        "LastWriteTime", "CreateNew", "Flush($true)", "Move-Item", "conflicting_duplicate",
        "stdout.txt", "stderr.txt", "firewall_pre.json", "firewall_post.json",
        "ReparsePoint", "OrdinalIgnoreCase", "repository_commit", "final_caller_exit_code",
    ):
        assert token in SCRIPT
    assert "New-NetFirewallRule" not in SCRIPT
    assert "Remove-NetFirewallRule" not in SCRIPT
    assert "[Parameter(Mandatory=$true)][string]$ExpectedRunId" in SCRIPT


def test_windows_publisher_never_uses_loose_prefix_cleanup():
    assert "DisplayName -like" not in SCRIPT
    assert "StartsWith($Root +" in SCRIPT
