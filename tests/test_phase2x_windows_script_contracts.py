import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
class WindowsScriptContracts(unittest.TestCase):
 def test_target_contracts_match_executable_sources_without_cross_wiring(self):
  targets=(('macd','NoraPhase2MacdRuntimeV2.mqh','NoraPhase2MacdTesterCanaryV2','nora_phase2u_macd_tester_v2.csv','NORA_PHASE2U_MACD_COMPLETE_V2'),('percentile','NoraPhase2PercentileRuntimeV2.mqh','NoraPhase2PercentileTesterCanaryV2','nora_phase2w_percentile_tester_v2.csv','NORA_PHASE2W_PERCENTILE_COMPLETE_V2'))
  for target,runtime,tester,csv,marker in targets:
   compile=(ROOT/f'phase-0a-h/windows/compile-{target}-tester-canary.ps1').read_text();execute=(ROOT/f'phase-0a-h/windows/execute-{target}-tester-canary.ps1').read_text()
   for token in (runtime,tester,csv,marker):self.assertIn(token,compile+execute)
   other='percentile' if target=='macd' else 'macd';self.assertNotIn(f'NoraPhase2{other.title()}',compile)
   self.assertNotIn('trade.',(compile+execute).lower())
