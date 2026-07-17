import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "phase-0a-h/windows/phase2-fresh-verifier-arguments.ps1"
HARNESS = ROOT / "tests/windows/phase2_fresh_verifier_argument_harness.ps1"
OPERATOR = ROOT / "phase-0a-h/windows/phase2-frt1r2-operator-qualification.ps1"


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


def test_operator_qualification_is_containment_only_and_fail_closed():
    source = OPERATOR.read_text()
    assert "-Action stage" in source and "-Action cleanup" in source
    assert "native_execution_started=$false" in source
    assert "history_accessed=$false" in source
    assert "market_data_accessed=$false" in source
    assert "Start-Process" not in source
    assert "CopyRates" not in source
