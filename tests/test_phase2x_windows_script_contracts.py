import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
class WindowsScriptContracts(unittest.TestCase):
 def test_target_contracts_match_executable_sources_without_cross_wiring(self):
  targets=(('macd','NoraPhase2MacdRuntimeV3.mqh','NoraPhase2MacdTesterCanaryV3'),('percentile','NoraPhase2PercentileRuntimeV3.mqh','NoraPhase2PercentileTesterCanaryV3'))
  for target,runtime,tester in targets:
   compile=(ROOT/f'phase-0a-h/windows/compile-{target}-tester-canary.ps1').read_text();execute=(ROOT/f'phase-0a-h/windows/execute-{target}-tester-canary.ps1').read_text()
   for token in (runtime,tester):self.assertIn(token,compile+execute)
   other='percentile' if target=='macd' else 'macd';self.assertNotIn(f'NoraPhase2{other.title()}',compile)
   self.assertNotIn('trade.',(compile+execute).lower())
   for field in ('contract_version','source_runtime_sha256','tester_source_sha256','metaeditor_executable_path','process_exit_status','compiler_success','warning_count','warning_count','error_count','compiler_log_sha256','expected_ex5_relative_path','ex5_exists','ex5_size','ex5_sha256','failure_reason'):
    self.assertIn(field,compile)
   self.assertIn("throw 'missing compiler'",compile);self.assertIn("throw 'missing compiler log'",compile);self.assertIn("throw 'stale EX5'",compile)
