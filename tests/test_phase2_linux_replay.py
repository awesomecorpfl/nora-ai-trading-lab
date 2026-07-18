import json
from pathlib import Path

from lab.phase2_linux_replay import run_linux_replay, verify_linux_replay


ROOT = Path(__file__).resolve().parents[1]


def test_complete_linux_replay_runs_twice_with_identical_stage_identities():
    first = run_linux_replay()
    second = run_linux_replay()
    assert verify_linux_replay(first)
    assert first == second
    assert first["classification"] == "PASS_LINUX_EXPERIMENT_REPLAY"
    assert list(first["stages"]) == [
        "ingestion",
        "aggregation",
        "indicators",
        "ast_intents",
        "simulation",
        "metrics",
    ]
    assert first["trades"]["trade_count"] >= 1


def test_committed_linux_replay_fixture_matches_runtime():
    fixture = ROOT / "tests/fixtures/phase2_linux_replay_fixture.json"
    committed = json.loads(fixture.read_text())
    assert committed == run_linux_replay()
    assert verify_linux_replay(committed)
