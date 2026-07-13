import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
class PackageBuilders(unittest.TestCase):
 def test_target_specific_atomic_and_closed_contracts(self):
  for target,columns in (('macd',"'row','close','macd','signal','histogram','pass'"),('percentile',"'row','source','percentile','pass'")):
   text=(ROOT/f'phase-0a-h/windows/build-{target}-returned-package.ps1').read_text()
   for token in ('returned_result_manifest.json','nora.phase2y.returned_package_v1','BatchIdentity','RunIdentifier','Get-FileHash','existing destination','missing collected file','compiler_success','runtime incomplete','Move-Item','Remove-Item',columns):
    self.assertIn(token,text)
   self.assertNotIn('CopyRates',text)
