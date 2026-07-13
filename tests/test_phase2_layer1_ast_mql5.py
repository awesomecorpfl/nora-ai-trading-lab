import json,subprocess,tempfile
from pathlib import Path
import pytest
from lab.mql5gen.layer1_batch import FAIL,MARKER,RUNTIME,TESTER,translate_feature_node
from lab.phase2_layer1_native import FIX,generated

ROOT=Path(__file__).resolve().parents[1];ENGINE=ROOT/'engine/target/debug/labengine'

def document(kind='ema',period=3):return {'schema_version':1,'root':{'kind':'compare','op':'gt','left':{'type':kind,'input':{'type':'series','name':'close'},'period':period},'right':{'kind':'number','value':0}}}

def test_selected_ast_nodes_cross_real_rust_canonicalization_boundary():
 identities=[]
 for kind in ('ema','highest','lowest'):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);task=root/'task.json';out=root/'ast.json';task.write_text(json.dumps({'task_version':1,'task_type':'canonicalize_ast','output_path':str(out),'ast':document(kind)}))
   result=json.loads(subprocess.run([ENGINE,task],check=True,capture_output=True,text=True).stdout);identities.append(result['ast_semantic_identity']);assert out.is_file()
 assert len(set(identities))==3
 with tempfile.TemporaryDirectory() as d:
  root=Path(d);task=root/'task.json';task.write_text(json.dumps({'task_version':1,'task_type':'canonicalize_ast','output_path':str(root/'x'),'ast':document('ema',0)}))
  assert subprocess.run([ENGINE,task],capture_output=True).returncode!=0

def test_translation_is_strict_deterministic_typed_and_nonsearchable():
 for kind in ('ema','highest','lowest'):
  node=document(kind)['root']['left'];a=translate_feature_node(node);assert a==translate_feature_node(node);assert a['output_name']=='value' and not a['grammar_admitted'] and not a['searchable']
 for bad in ({'type':'ema','input':{'type':'series','name':'close'},'period':0},{'type':'ema','input':{'type':'boolean','name':'x'},'period':3},{'type':'ema','input':{'type':'series','name':'x'},'period':3,'extra':1}):
  with pytest.raises(ValueError):translate_feature_node(bad)

def test_generated_sources_are_deterministic_embedded_and_static_safe():
 p1,d1=generated();p2,d2=generated();assert p1==p2 and d1==d2
 source=(d1[RUNTIME]+d1[TESTER]).decode()
 for required in ('NoraLayer1Compute','EMA','Highest','Lowest',MARKER,FAIL):assert required in source
 for forbidden in ('TimeCurrent','TimeTradeServer','CopyRates','CopyBuffer','iMA(','iHighest','iLowest','SymbolInfo','OrderSend','CTrade','MathRand','expected_'):assert forbidden not in source
 assert p1['reference_modes'] and not p1['native_execution_attempted'] and not p1['searchable']
