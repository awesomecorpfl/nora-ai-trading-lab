import json
from pathlib import Path
from lab.native_targets import EXECUTION_TARGET,TIME_RULE_TARGET
from lab.phase2_execution_batch import build,preflight
from lab.phase2_execution_compile_contract import build_compile_input
from lab.mql5gen.execution import generate

ROOT=Path(__file__).resolve().parents[1]
def test_execution_descriptor_is_distinct_and_accepted_artifacts_remain_readable(tmp_path):
 assert EXECUTION_TARGET.identity != TIME_RULE_TARGET.identity
 assert EXECUTION_TARGET.target_identifier == "execution"
 assert TIME_RULE_TARGET.reconciliation_implementation == "nora.time_rule_native_reconciliation_v1"
 accepted=json.loads((ROOT/'tests/fixtures/phase2_execution_native_accepted/native_acceptance.json').read_text())
 assert accepted['native_parity_accepted'] is True
 assert accepted['execution_packet_identity']=='b9f7844c8edc9937e7207616839aa0dd918989c32b395ac674e28b4b92955ec0'
 assert accepted['final_native_batch_identity']=='66323ef3c96351a841cca814c699f44e50a74fe3db3a51ec75d6e3f7aa47405f'

def test_execution_generation_and_precompile_semantics_are_unchanged(tmp_path):
 out=tmp_path/'generated';out.mkdir();p=generate(ROOT/'tests/fixtures/phase2_execution_rust_evidence.json',out)
 assert p['runtime_identity']=='8d911b007638c8cecf61cb0fa1722f1783c1c0e4d2a72020339de067c2391534'
 assert p['tester_identity']=='24c6f824e261f0027d5d660a4f71495c2d472d667d8fbcf1ff6aeafecebc09df'
 assert p['package_identity']=='a221674db430a58bf8f0479014b530a11697341f2904439f0d9325829566f8f0'
 assert build_compile_input()['compile_input_identity']=='065d1e113aa04d68976ea0c363399197c7126f7873817cbd5829f8f69bfbf859'
 assert build()['batch_identity']=='c1e272300a7aa319f51aa1b11876792ce96d15fcdac4b5636109b22e18462fa8'
 assert preflight()['status']=='PASS'
