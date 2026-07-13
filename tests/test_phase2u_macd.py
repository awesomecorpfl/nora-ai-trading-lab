import json,tempfile,unittest
from pathlib import Path
from lab.mql5gen.macd import *
import lab.mql5gen.macd as subject
class TestMacd(unittest.TestCase):
 def test_repeatable_and_isolated(self):
  with tempfile.TemporaryDirectory() as a,tempfile.TemporaryDirectory() as b:
   x,y=Path(a),Path(b);ra,rb=generate(x),generate(y)
   self.assertEqual(ra,rb)
   for n in (RUNTIME,TESTER,EVIDENCE,PACKAGE):self.assertEqual((x/n).read_bytes(),(y/n).read_bytes())
   e=json.loads((x/EVIDENCE).read_text());self.assertEqual(e['task_semantic_identity'],TASK_ID);self.assertEqual(e['signal_input'],'compact ordered non-null MACD sequence realigned to original rows');self.assertEqual(e['macd'][:3],[None]*3);self.assertEqual(e['signal'][:5],[None]*5)
   self.assertEqual(e['rust_macd_component_identity'],'fef4a9583d0a12d5f067be9d977015a4f6d441e20232d2e8241b6a5539eee6f9')
   runtime=(x/RUNTIME).read_text();tester=(x/TESTER).read_text()
   self.assertIn('NoraPhase2MacdCompute',runtime);self.assertIn('NoraMacdEma',runtime);self.assertIn('MathIsValidNumber',runtime)
   self.assertNotIn(' &input[]',runtime);self.assertIn(' &values[]',runtime)
   self.assertIn('int OnInit()',tester);self.assertIn('FileWrite',tester);self.assertIn('NORA_PHASE2U_MACD_COMPLETE_V3',tester);self.assertIn('return "NULL"',tester)
   self.assertEqual(e['csv_schema'],['row','close','macd','signal','histogram','pass'])
   self.assertEqual(e['csv_null_token'],'NULL')
 def test_atomic_existing_target(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/RUNTIME).write_text('x')
   with self.assertRaises(GenerationError):generate(p)
   self.assertEqual((p/RUNTIME).read_text(),'x');self.assertFalse((p/EVIDENCE).exists())
 def test_source_and_period_mutations_change_component_identities(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d); baseline=generate(root/'base') if (root/'base').mkdir() is None else None
   original_close,original_task=subject.CLOSE,subject.TASK_ID
   try:
    subject.CLOSE=[1.1004,*original_close[1:]]
    (root/'early').mkdir(); early=generate(root/'early')
    self.assertNotEqual(early['executable_contract_identity'],baseline['executable_contract_identity'])
    self.assertNotEqual(early['tester_identity'],baseline['tester_identity'])
    subject.CLOSE=[*original_close[:-1],1.1030]
    (root/'late').mkdir(); late=generate(root/'late')
    self.assertNotEqual(late['executable_contract_identity'],baseline['executable_contract_identity'])
    subject.TASK_ID='0'*64
    (root/'task').mkdir(); changed=generate(root/'task')
    self.assertNotEqual(changed['package_identity'],baseline['package_identity'])
   finally: subject.CLOSE,subject.TASK_ID=original_close,original_task
 def test_runtime_tester_package_identity_mutation_detection(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'one').mkdir();base=generate(p/'one')
   original=subject.VERSION
   try:
    subject.VERSION='nora.phase2u.macd_v1_mutated'
    (p/'two').mkdir();mutated=generate(p/'two')
    self.assertNotEqual(mutated['runtime_identity'],base['runtime_identity'])
    self.assertNotEqual(mutated['tester_identity'],base['tester_identity'])
    self.assertNotEqual(mutated['package_identity'],base['package_identity'])
   finally: subject.VERSION=original
 def test_atomic_staged_publication_failure(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d); original=subject._publish; calls=[]
   def fail(directory,name,data):
    calls.append(name)
    if name==TESTER: raise GenerationError('injected publication failure')
    return original(directory,name,data)
   subject._publish=fail
   try:
    with self.assertRaises(GenerationError): generate(p)
   finally: subject._publish=original
   self.assertEqual(calls[:2],[RUNTIME,TESTER])
   for name in (EVIDENCE,RUNTIME,TESTER,PACKAGE): self.assertFalse((p/name).exists())
 def test_expected_vector_mutation_changes_tester_and_package_without_native_claim(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'base').mkdir();base=generate(p/'base');original=subject.MACD
   try:
    subject.MACD=[*original[:-1],0.0];(p/'mut').mkdir();mut=generate(p/'mut')
    self.assertNotEqual(mut['tester_identity'],base['tester_identity']);self.assertNotEqual(mut['package_identity'],base['package_identity'])
    self.assertFalse(mut['native_parity']);self.assertFalse(mut['grammar_admitted']);self.assertFalse(mut['searchable'])
   finally: subject.MACD=original
 def test_verify_package_binding_detects_mismatches(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);generate(p)
   pkg=json.loads((p/PACKAGE).read_text());ev=json.loads((p/EVIDENCE).read_text())
   rt=(p/RUNTIME).read_bytes();ts=(p/TESTER).read_bytes()
   self.assertEqual(verify_package_binding(pkg,rt,ts,ev['executable_contract_identity'],ev['periods']),[])
   forged=dict(pkg);forged['runtime_sha256']='0'*64
   self.assertIn('runtime_sha256',verify_package_binding(forged,rt,ts,ev['executable_contract_identity'],ev['periods']))
   forged2=dict(pkg);forged2['package_identity']='0'*64
   self.assertIn('package_identity',verify_package_binding(forged2,rt,ts,ev['executable_contract_identity'],ev['periods']))
