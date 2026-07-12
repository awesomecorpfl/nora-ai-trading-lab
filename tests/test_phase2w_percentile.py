import tempfile,unittest
from pathlib import Path
from lab.mql5gen.percentile import *
import lab.mql5gen.percentile as subject
class TestPercentile(unittest.TestCase):
 def test_deterministic_isolated_and_atomic(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'a').mkdir();(p/'b').mkdir();a=generate(p/'a');b=generate(p/'b');self.assertEqual(a,b)
   for n in (RUNTIME,TESTER,EVIDENCE,PACKAGE):self.assertEqual((p/'a'/n).read_bytes(),(p/'b'/n).read_bytes())
   (p/'c').mkdir();(p/'c'/RUNTIME).write_text('x')
   with self.assertRaises(GenerationError):generate(p/'c')
   self.assertFalse((p/'c'/EVIDENCE).exists())
 def test_source_lookback_semantic_and_identity_mutations(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'a').mkdir();base=generate(p/'a'); original,original_output=subject.INPUT,subject.OUTPUT
   try:
    subject.INPUT=[*original[:-1],1.1030];(p/'b').mkdir();mut=generate(p/'b');self.assertNotEqual(mut['rust_percentile_identity'],base['rust_percentile_identity'])
    subject.INPUT=original
    subject.OUTPUT=[*subject.OUTPUT[:-1],0.5]
    (p/'c').mkdir();contract=generate(p/'c');self.assertNotEqual(contract['package_identity'],base['package_identity'])
   finally: subject.INPUT,subject.OUTPUT=original,original_output
 def test_runtime_tester_and_package_mutations(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'a').mkdir();base=generate(p/'a');original=subject.INPUT_ID
   try:
    subject.INPUT_ID='0'*64;(p/'b').mkdir();mut=generate(p/'b');self.assertNotEqual(mut['runtime_identity'],base['runtime_identity']);self.assertNotEqual(mut['tester_identity'],base['tester_identity']);self.assertNotEqual(mut['package_identity'],base['package_identity'])
   finally: subject.INPUT_ID=original
 def test_excludes_bundled_sma_and_slope(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);generate(p);e=json.loads((p/EVIDENCE).read_text());self.assertNotIn('slope',json.dumps(e));self.assertNotIn('sma3.percentile4.slope',json.dumps(e))
 def test_injected_publication_failure_cleans_all(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);original=subject._publish
   def fail(directory,name,data):
    if name==TESTER: raise GenerationError('injected')
    return original(directory,name,data)
   subject._publish=fail
   try:
    with self.assertRaises(GenerationError):generate(p)
   finally: subject._publish=original
   for name in (RUNTIME,TESTER,EVIDENCE,PACKAGE):self.assertFalse((p/name).exists())
