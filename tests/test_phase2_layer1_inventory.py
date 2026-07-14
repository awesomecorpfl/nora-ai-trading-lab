import json
from pathlib import Path

from lab.phase2_execution import sha
from lab.phase2_layer1_inventory import SELECTED,batch_plan,dependency_map,matrix

ROOT=Path(__file__).resolve().parents[1];FIX=ROOT/'tests/fixtures/phase2_layer1_first_batch'

def test_authoritative_inventory_has_every_locked_node_and_complete_fields():
 value=matrix();assert value==json.loads((FIX/'authoritative_matrix.json').read_text())
 assert len(value['nodes'])==22 and value['counts']['ACCEPTED']==10 and value['counts']['IMPLEMENTED_UNPROVED']==12
 required={'canonical_id','canonical_identity','rust','typed_ast','outputs','null_warmup_semantics','mql5_translation','local_fixture','native_compiler_evidence','native_result','native_reconciliation','grammar_admission','searchable','dependencies','remaining_gap'}
 assert all(required<=set(x) and not x['searchable'] for x in value['nodes'])
 assert {x['canonical_id'] for x in value['nodes'] if x['first_batch']}==set(SELECTED)

def test_ten_strategy_dependency_map_is_narrow_and_frozen():
 value=dependency_map();assert value==json.loads((FIX/'dependency_map.json').read_text())
 assert len(value['strategies'])==10 and {x['family'] for x in value['strategies']}=={'trend-pullback','close-confirmed breakout'}
 assert value['blocking_nodes']==[] and set(value['accepted_batch_nodes'])==set(SELECTED) and not value['multi_output_dependencies']
 assert {'layer1.session_ohlc','layer1.vwap'}<=set(value['not_needed_before_first_ten'])

def test_batch_plan_selects_only_three_unaccepted_families():
 m=matrix();ids={x['canonical_id']:x['canonical_identity'] for x in m['nodes'] if x['first_batch']};value=batch_plan(ids)
 assert value==json.loads((FIX/'batch_plan.json').read_text()) and value['selected_nodes']==list(SELECTED)
 assert all(x['mode']=='independent_generated' and x['shift']==0 for x in value['reference_modes'].values())
 assert not value['grammar_admitted'] and not value['searchable']
