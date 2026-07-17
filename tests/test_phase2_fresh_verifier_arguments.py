import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "phase-0a-h/windows/phase2-fresh-verifier-arguments.ps1"
HARNESS = ROOT / "tests/windows/phase2_fresh_verifier_argument_harness.ps1"


def test_production_uses_authoritative_fresh_verifier_argument_builder():
    containment = (ROOT / "phase-0a-h/windows/phase2-network-containment.ps1").read_text()
    assert HELPER.name in containment
    assert "New-NoraFreshVerifierArgumentVector" in containment
    assert "@args" not in containment


def test_windows_strict_mode_child_boundary_harness():
    powershell = shutil.which("powershell") or shutil.which("pwsh")
    if not powershell:
        pytest.skip("PowerShell 5.1 unavailable on this Linux host")
    result = subprocess.run(
        [powershell, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
         "-File", str(HARNESS), "-HelperPath", str(HELPER)],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert '"status":"PASS"' in result.stdout
    assert '"conflicting_vector_rejected":true' in result.stdout
