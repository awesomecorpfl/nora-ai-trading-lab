import json,tempfile,unittest
from pathlib import Path
from lab.mql5gen.execution import generate,RUNTIME,TESTER,PACKAGE,CSV,MARKER
ROOT=Path(__file__).resolve().parents[1]; EVIDENCE=ROOT/'tests/fixtures/phase2_execution_rust_evidence.json'
class ExecutionMql5(unittest.TestCase):
 def test_repeatable_and_bound(self):
  with tempfile.TemporaryDirectory() as d:
   a=Path(d)/'a';b=Path(d)/'b';a.mkdir();b.mkdir();x=generate(EVIDENCE,a);y=generate(EVIDENCE,b)
   self.assertEqual(x,y)
   for n in (RUNTIME,TESTER,PACKAGE):self.assertEqual((a/n).read_bytes(),(b/n).read_bytes())
   self.assertEqual(x['result_filename'],CSV);self.assertEqual(x['completion_marker'],MARKER);self.assertFalse(x['grammar_admitted']);self.assertFalse(x['searchable'])
 def test_static_safety_and_event_entrypoint(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d);generate(EVIDENCE,out);src=((out/RUNTIME).read_text()+'\n'+(out/TESTER).read_text()).lower()
   for forbidden in ('ordersend','cTrade'.lower(),'position','account','copyrates','itime','iclose','indicator','itimecurrent','timelocal','mathrand','chart') : self.assertNotIn(forbidden,src)
   self.assertIn('int oninit()',src);self.assertIn('noraexecutionresolvev1',src);self.assertIn('no_trade',src)
 def test_atomic_failure_cleanup(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d);out.joinpath(RUNTIME).write_text('occupied')
   with self.assertRaises(ValueError):generate(EVIDENCE,out)
   self.assertEqual(list(out.iterdir()),[out/RUNTIME])
