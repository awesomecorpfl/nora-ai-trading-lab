from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/phase2-exit-propagation-batch"


def run(*specs):
    return subprocess.run([str(SCRIPT), *specs], text=True, capture_output=True)


def test_expected_nonzero_and_later_success_preserve_machine_status():
    result = run("1:exit 1", "0:exit 0")
    assert result.returncode == 0
    assert "CASE=1 EXIT=1 EXPECTED=1" in result.stdout
    assert "CASE=2 EXIT=0 EXPECTED=0" in result.stdout


def test_unexpected_failure_is_aggregate_nonzero():
    result = run("0:exit 1", "0:exit 0")
    assert result.returncode == 1
    assert "CASE=1 EXIT=1 EXPECTED=0" in result.stdout


def test_stdout_and_stderr_are_separate():
    result = run("37:printf out; printf err >&2; exit 37")
    assert result.returncode == 0
    assert "out" in result.stdout and "err" not in result.stdout
    assert "err" in result.stderr


def test_blank_or_malformed_spec_fails_closed():
    assert run("1:").returncode == 2
    assert run("bad:exit 1").returncode == 2
