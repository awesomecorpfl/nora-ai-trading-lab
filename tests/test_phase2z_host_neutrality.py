import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class HostNeutrality(unittest.TestCase):
 def test_generated_canaries_are_market_and_state_inert(self):
  forbidden=('CopyRates','CopyOpen','CopyHigh','CopyLow','CopyClose','CopyTicks','iMACD','iMA','Position','Order','Account','TimeCurrent','TimeLocal','MathRand','Object','GlobalVariable','Open[','High[','Low[','Close[','Volume[')
  for source in (ROOT/'tests/fixtures/phase2u_macd/NoraPhase2MacdTesterCanaryV3.mq5',ROOT/'tests/fixtures/phase2w_percentile/NoraPhase2PercentileTesterCanaryV3.mq5'):
   text=source.read_text()
   for token in forbidden:self.assertNotIn(token,text)
   self.assertIn('OnInit',text);self.assertIn('FileWrite',text)
 def test_two_context_contract_is_explicit(self):
  text=(ROOT/'tests/fixtures/phase2x_host_contexts_v1.json').read_text()
  self.assertIn('GDAXI',text);self.assertIn('DISCOVER_READ_ONLY',text);self.assertIn('identical fixed vectors',text)
