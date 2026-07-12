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
    self.assertNotEqual(early['rust_macd_component_identity'],baseline['rust_macd_component_identity'])
    self.assertNotEqual(early['tester_identity'],baseline['tester_identity'])
    subject.CLOSE=[*original_close[:-1],1.1030]
    (root/'late').mkdir(); late=generate(root/'late')
    self.assertNotEqual(late['rust_macd_component_identity'],baseline['rust_macd_component_identity'])
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
