import tempfile,unittest
from pathlib import Path
from lab.mql5gen.percentile import *
class TestPercentile(unittest.TestCase):
 def test_deterministic_isolated_and_atomic(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'a').mkdir();(p/'b').mkdir();a=generate(p/'a');b=generate(p/'b');self.assertEqual(a,b)
   for n in (RUNTIME,TESTER,EVIDENCE,PACKAGE):self.assertEqual((p/'a'/n).read_bytes(),(p/'b'/n).read_bytes())
   (p/'c').mkdir();(p/'c'/RUNTIME).write_text('x')
   with self.assertRaises(GenerationError):generate(p/'c')
   self.assertFalse((p/'c'/EVIDENCE).exists())
