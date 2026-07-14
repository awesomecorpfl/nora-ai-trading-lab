import copy,json,subprocess
from pathlib import Path
import pytest
from lab.phase2_execution import sha
from lab.phase2_ten_strategy import FIX,experiment_bundle,replay_record,run_rust_task,rust_evidence,rust_task_spec


def test_real_rust_boundary_matches_frozen_evidence():
    output=run_rust_task();evidence=rust_evidence(output)
    assert evidence==json.loads((FIX/"rust_evidence.json").read_text())
    assert len(output["strategy_outputs"])==10 and output["schema_version"]=="nora.phase2_ten_strategy_rust_output_v1"
    assert all(len(x["trades"])>=1 for x in output["strategy_outputs"])


def test_linux_replay_three_destinations_is_semantically_exact():
    outputs=[run_rust_task() for _ in range(3)];evidence=rust_evidence(outputs[0]);record=replay_record(outputs,evidence)
    assert record==json.loads((FIX/"replay_record.json").read_text())
    assert record["classification"]=="PASS_STRATEGY_SUITE_REPLAY" and record["destination_inert"]
    assert record["gate_scope"].startswith("strategy-suite replay evidence")


def test_bundle_is_frozen_and_expected_ledger_mutation_changes_identity():
    evidence=rust_evidence();bundle=experiment_bundle(evidence)
    assert bundle==json.loads((FIX/"experiment_bundle.json").read_text())
    changed=copy.deepcopy(evidence);changed["expected_ledger_vector_identities"]["trend_pullback_1"]="changed";changed.pop("combined_rust_evidence_identity")
    assert sha(changed)!=evidence["combined_rust_evidence_identity"]


def test_rust_task_rejects_strategy_fixture_binding_mutation(tmp_path):
    task=rust_task_spec();task.pop("rust_suite_task_identity");task["fixtures"]["segments"][0]["strategy_identity"]="wrong"
    path=tmp_path/"task.json";path.write_text(json.dumps(task));result=subprocess.run(["engine/target/debug/labengine",str(path)],text=True,capture_output=True)
    assert result.returncode==2 and "strategy fixture binding" in result.stderr
