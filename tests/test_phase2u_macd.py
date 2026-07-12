import json,tempfile,unittest
from pathlib import Path
from lab.mql5gen.macd import *
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
