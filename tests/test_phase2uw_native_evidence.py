"""Validation tests for committed MACD and Percentile native evidence packages."""
import csv,hashlib,json,math,unittest
from pathlib import Path
from lab.phase2x_batch import load,canon,sha
from lab.phase2z_metaeditor_policy import evaluate as evaluate_policy

MACD_DIR=Path('tests/fixtures/phase2u_macd_native')
PCT_DIR=Path('tests/fixtures/phase2w_percentile_native')
RUN_DIRS=['gdaxi_m1_1','gdaxi_m1_2','audcad_m1_1','audcad_m1_2']
MACD_FILES=['execution.json','nora_phase2u_macd_tester_v3.csv','tester-journal.log','tester.ini','tester.ini.normalized','lifecycle.jsonl','tester.log']
PCT_FILES=['execution.json','nora_phase2w_percentile_tester_v3.csv','tester-journal.log','tester.ini','tester.ini.normalized','lifecycle.jsonl','tester.log']

def _read_json(path):
 return json.loads(Path(path).read_text(encoding='utf-8-sig'))

class TestNativeEvidenceCompleteness(unittest.TestCase):
 def test_all_eight_run_directories_exist_with_required_files(self):
  for d,label,files in [(MACD_DIR,'macd',MACD_FILES),(PCT_DIR,'percentile',PCT_FILES)]:
   for run in RUN_DIRS:
    rdir=d/run
    self.assertTrue(rdir.is_dir(),f'{label}/{run} missing')
    for f in files:
     self.assertTrue((rdir/f).is_file(),f'{label}/{run}/{f} missing')
 def test_no_unexpected_files_in_run_dirs(self):
  for d,label,files in [(MACD_DIR,'macd',MACD_FILES),(PCT_DIR,'percentile',PCT_FILES)]:
   for run in RUN_DIRS:
    actual={p.name for p in (d/run).iterdir() if p.is_file()}
    self.assertEqual(actual,set(files),f'{label}/{run} has unexpected files: {actual-set(files)}')
 def test_compile_evidence_complete(self):
  for d,label in [(MACD_DIR,'macd'),(PCT_DIR,'percentile')]:
   cdir=d/'compile'
   self.assertTrue((cdir/'compile.json').is_file())
   self.assertTrue((cdir/'compile.log').is_file())
   self.assertTrue(any(cdir.glob('*.ex5')))
   self.assertTrue(any(cdir.glob('*.mqh')))
   self.assertTrue(any(cdir.glob('*.mq5')))
   self.assertTrue((d/'native_evidence_manifest.json').is_file())

class TestNativeEvidenceBinding(unittest.TestCase):
 def test_compile_record_proves_source_and_ex5_binding(self):
  batch=load()
  for d,t in [(MACD_DIR,next(t for t in batch['targets'] if t['id']=='macd')),(PCT_DIR,next(t for t in batch['targets'] if t['id']=='percentile'))]:
   cj=_read_json(d/'compile'/'compile.json')
   self.assertEqual(cj['metaeditor_version'],'5.0.0.5836')
   self.assertEqual(cj['raw_process_exit_status'],1)
   self.assertTrue(cj['compiler_success'])
   self.assertEqual(cj['error_count'],0)
   self.assertEqual(cj['warning_count'],0)
   self.assertFalse(cj['preexisting_ex5'])
   self.assertTrue(cj['ex5_exists'])
   # Source hashes match actual files on disk
   rt_actual=hashlib.sha256((d/'compile'/cj['source_runtime_path'].split('/')[-1]).read_bytes()).hexdigest()
   ts_actual=hashlib.sha256((d/'compile'/cj['tester_source_path'].split('/')[-1]).read_bytes()).hexdigest()
   self.assertEqual(rt_actual,cj['source_runtime_sha256'])
   self.assertEqual(ts_actual,cj['tester_source_sha256'])
   # EX5 hash matches
   ex5_actual=hashlib.sha256((d/'compile'/cj['expected_ex5_relative_path'].split('/')[-1]).read_bytes()).hexdigest()
   self.assertEqual(ex5_actual,cj['ex5_sha256'])
   # Policy acceptance
   rec={'exit':cj['raw_process_exit_status'],'metaeditor_version':cj['metaeditor_version'],
        'checks':{'version':True,'source':True,'log_complete':cj['compiler_log_complete'],'zero_errors':True,'zero_warnings':True,'fresh_ex5':True,'expected_ex5_path':True,'hashes_match':True}}
   ok,_=evaluate_policy(rec);self.assertTrue(ok)
 def test_source_hashes_match_corrected_package(self):
  batch=load()
  for d,t,label in [(MACD_DIR,next(t for t in batch['targets'] if t['id']=='macd'),'macd'),(PCT_DIR,next(t for t in batch['targets'] if t['id']=='percentile'),'percentile')]:
   cj=_read_json(d/'compile'/'compile.json')
   pkg=_read_json(f'tests/fixtures/phase2{"u" if label=="macd" else "w"}_{label}/phase2{"u" if label=="macd" else "w"}_{label}_executable_package.json')
   self.assertEqual(cj['source_runtime_sha256'],pkg['runtime_sha256'],f'{label} runtime sha mismatch between compile record and package')
   self.assertEqual(cj['tester_source_sha256'],pkg['tester_sha256'],f'{label} tester sha mismatch between compile record and package')

class TestNativeEvidenceDivergence(unittest.TestCase):
 def test_all_runs_pass_exact_or_within_tolerance(self):
  batch=load()
  for d,t in [(MACD_DIR,next(t for t in batch['targets'] if t['id']=='macd')),(PCT_DIR,next(t for t in batch['targets'] if t['id']=='percentile'))]:
   ev=t['expected_vectors']
   fields=[f for f in ev['vectors'] if f not in ('row','close','source','null_masks')]
   csv_name=t['result_filename']
   for run in RUN_DIRS:
    text=(d/run/csv_name).read_text()
    rows=list(csv.reader(text.splitlines(),delimiter='\t',strict=True))
    header=rows[0]
    pidx=header.index('pass')
    self.assertTrue(all(r[pidx].strip()=='true' for r in rows[1:]),f'{t["id"]}/{run} not all pass')
    for field in fields:
     fidx=header.index(field)
     expected=ev['vectors'][field]
     null_mask=ev['vectors'].get('null_masks',{}).get(field,[])
     actual_nulls=[r[fidx].strip()=='NULL' for r in rows[1:]]
     self.assertEqual(actual_nulls,null_mask,f'{t["id"]}/{run}/{field} null mismatch')
     for i,r in enumerate(rows[1:]):
      raw=r[fidx].strip()
      if raw=='NULL':continue
      self.assertLessEqual(abs(float(raw)-expected[i]),1e-12+1e-9*abs(expected[i]))

class TestNativeEvidenceRepeatability(unittest.TestCase):
 def test_all_csvs_byte_identical_per_target(self):
  for d,csv_name in [(MACD_DIR,'nora_phase2u_macd_tester_v3.csv'),(PCT_DIR,'nora_phase2w_percentile_tester_v3.csv')]:
   hashes=set()
   for run in RUN_DIRS:
    hashes.add(hashlib.sha256((d/run/csv_name).read_bytes()).hexdigest())
   self.assertEqual(len(hashes),1)
 def test_all_runs_have_unique_execution_records(self):
  for d in [MACD_DIR,PCT_DIR]:
   hashes=set()
   for run in RUN_DIRS:
    hashes.add(hashlib.sha256((d/run/'execution.json').read_bytes()).hexdigest())
   self.assertEqual(len(hashes),4)

class TestNativeEvidenceStalePercentilePackage(unittest.TestCase):
 def test_stale_package_identity_not_current(self):
  batch=load()
  pct_target=next(t for t in batch['targets'] if t['id']=='percentile')
  pkg=_read_json('tests/fixtures/phase2w_percentile/phase2w_percentile_executable_package.json')
  stale=pkg['stale_content_binding_identities']
  self.assertNotEqual(stale['package_identity'],pct_target['package_identity'])
  self.assertNotEqual(stale['runtime_identity_claim'],pct_target['runtime_identity'])
  self.assertNotEqual(stale['tester_identity_claim'],pct_target['tester_identity'])
 def test_corrected_package_identity_is_content_derived(self):
  from lab.mql5gen.percentile import verify_package_binding
  pkg=_read_json('tests/fixtures/phase2w_percentile/phase2w_percentile_executable_package.json')
  ev=_read_json('tests/fixtures/phase2w_percentile/phase2w_percentile_executable_rust_evidence.json')
  rt=Path('tests/fixtures/phase2w_percentile/NoraPhase2PercentileRuntimeV3.mqh').read_bytes()
  ts=Path('tests/fixtures/phase2w_percentile/NoraPhase2PercentileTesterCanaryV3.mq5').read_bytes()
  self.assertEqual(verify_package_binding(pkg,rt,ts,ev['executable_contract_identity']),[])
 def test_compile_record_hashes_match_corrected_not_stale(self):
  cj=_read_json(PCT_DIR/'compile'/'compile.json')
  pkg=_read_json('tests/fixtures/phase2w_percentile/phase2w_percentile_executable_package.json')
  self.assertEqual(cj['source_runtime_sha256'],pkg['runtime_sha256'])
  self.assertEqual(cj['tester_source_sha256'],pkg['tester_sha256'])

class TestNativeEvidenceImmutability(unittest.TestCase):
 def test_manifest_semantic_identity_recomputes(self):
  for d in [MACD_DIR,PCT_DIR]:
   manifest=_read_json(d/'native_evidence_manifest.json')
   stored=manifest['evidence_semantic_identity']
   copy=dict(manifest);copy.pop('evidence_semantic_identity',None)
   self.assertEqual(stored,sha(canon(copy)))
 def test_no_trading_operation_in_journals(self):
  for d,csv_name in [(MACD_DIR,'nora_phase2u_macd_tester_v3.csv'),(PCT_DIR,'nora_phase2w_percentile_tester_v3.csv')]:
   for run in RUN_DIRS:
    journal=(d/run/'tester-journal.log').read_text()
    self.assertNotIn('trade',journal.lower())
    self.assertNotIn('order',journal.lower())
