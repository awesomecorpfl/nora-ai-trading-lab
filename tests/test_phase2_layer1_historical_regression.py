import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def _load(path):return json.loads((ROOT/path).read_text())

def test_accepted_native_identities_and_flags_are_unchanged_and_readable():
 execution=_load('tests/fixtures/phase2_execution_native_accepted/native_acceptance.json')
 time=_load('tests/fixtures/phase2_time_rule_native_accepted/native_acceptance.json')
 macd=_load('tests/fixtures/phase2u_macd_native/native_evidence_manifest.json')
 percentile=_load('tests/fixtures/phase2w_percentile_native/native_evidence_manifest.json')
 slope=_load('tests/fixtures/phase2n_mql5_slope_native/native_evidence_manifest.json')
 layer1=_load('tests/fixtures/phase2_layer1_first_batch/native_accepted/native_acceptance.json')
 matrix=_load('tests/fixtures/phase2_layer1_first_batch/authoritative_matrix.json')
 assert execution['acceptance_identity']=='2e8312d5a1ffca744f916982376cfab6fec2c167b1d349b749fe09b057252029'
 assert time['acceptance_identity']=='fd15de7bb0631131cfa530e7caf3594b8ee6a34b1b7b021d1ba15b9c0afc3621'
 assert macd['evidence_semantic_identity']=='2717ce8650e0c820c9b3fd4e6abd227ddbc5dced74d421eea68be079221c6a1e'
 assert percentile['evidence_semantic_identity']=='438442095775a503c20ca397d9fce00858f70b7df0d799488c8269f8202029b8'
 assert slope['semantic_result_identity']=='221f85942998674cd79537ce0e1396535361f7159f931fc2507e2f3b7f4f033f'
 assert layer1['acceptance_identity']=='3fe6ce82622ad0a0fa01e887e4745a02bfcb8e1ff5e0899f37e3108e50687cdb'
 assert layer1['native_parity_accepted'] and matrix['matrix_identity']=='8c842057b6d9efebbfd17ffaf583f4058d7464816f29d078d80db3403768b3bf'
 assert matrix['counts']['ACCEPTED']==10 and matrix['counts']['IMPLEMENTED_UNPROVED']==12
 for accepted in (execution,time,layer1):assert accepted['native_parity_accepted'] and not accepted['grammar_admitted'] and not accepted['searchable']
