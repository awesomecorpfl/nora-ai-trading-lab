"""Local-only deterministic native-validation handoff for Phase-2X."""
from __future__ import annotations
import hashlib,json,shutil,tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; VERSION='nora.phase2x.native_batch_v1'
TARGETS=(
 ('macd','tests/fixtures/phase2u_macd/phase2u_macd_executable_package.json','tests/fixtures/phase2u_macd/NoraPhase2MacdRuntimeV2.mqh','tests/fixtures/phase2u_macd/NoraPhase2MacdTesterCanaryV2.mq5','phase-0a-h/windows/compile-macd-tester-canary.ps1','phase-0a-h/windows/execute-macd-tester-canary.ps1'),
 ('percentile','tests/fixtures/phase2w_percentile/phase2w_percentile_executable_package.json','tests/fixtures/phase2w_percentile/NoraPhase2PercentileRuntimeV2.mqh','tests/fixtures/phase2w_percentile/NoraPhase2PercentileTesterCanaryV2.mq5','phase-0a-h/windows/compile-percentile-tester-canary.ps1','phase-0a-h/windows/execute-percentile-tester-canary.ps1'),)
def _canon(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode()
def _sha(data):return hashlib.sha256(data).hexdigest()
def manifest():
 targets=[]
 for ident,pkg,runtime,tester,compile_script,execute_script in TARGETS:
  package=json.loads((ROOT/pkg).read_text()); evidence_path=Path(pkg).with_name(Path(pkg).name.replace('_package.json','_rust_evidence.json'))
  evidence=json.loads((ROOT/evidence_path).read_text())
  targets.append({'id':ident,'version':package['version'],'package_path':pkg,'package_identity':package['package_identity'],'runtime_path':runtime,'runtime_identity':package['runtime_identity'],'tester_path':tester,'tester_identity':package['tester_identity'],'rust_task_identity':evidence['task_semantic_identity'],'rust_component_identity':package.get('rust_macd_component_identity',package.get('rust_percentile_identity')),'expected_vectors':{'row_count':evidence['row_count']},'csv_filename':package['csv_filename'],'completion_marker':package['completion_marker'],'compile_script':compile_script,'execute_script':execute_script,'native_parity':False,'grammar_admitted':False,'searchable':False})
 result={'schema_version':VERSION,'target_order':[x[0] for x in TARGETS],'targets':targets,'forbidden_unexpected_files':True,'numeric_tolerance':1e-12}
 result['batch_identity']=_sha(_canon(result));return result
def preflight(report):
 value=manifest();errors=[]
 for target in value['targets']:
  for key in ('package_path','runtime_path','tester_path','compile_script','execute_script'):
   if not (ROOT/target[key]).is_file():errors.append('missing:'+target[key])
  package=json.loads((ROOT/target['package_path']).read_text())
  if package['package_identity']!=target['package_identity'] or package['runtime_identity']!=target['runtime_identity'] or package['tester_identity']!=target['tester_identity']:errors.append('stale:'+target['id'])
  if target['native_parity'] or target['grammar_admitted'] or target['searchable']:errors.append('invalid-state:'+target['id'])
 output={'status':'PASS' if not errors else 'FAIL','batch_identity':value['batch_identity'],'errors':errors};p=Path(report);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_bytes(_canon(output)+b'\n');tmp.replace(p);return output
def stage(destination,inject_failure=False):
 dest=Path(destination)
 if dest.exists():raise ValueError('existing target refused')
 value=manifest();pre=preflight(dest.parent/'.phase2x-preflight.json')
 if pre['status']!='PASS':raise ValueError('preflight failed')
 tmp=Path(tempfile.mkdtemp(prefix='.phase2x-',dir=dest.parent))
 try:
  (tmp/'batch.json').write_bytes(_canon(value)+b'\n')
  for target in value['targets']:
   folder=tmp/'targets'/target['id'];folder.mkdir(parents=True)
   for key in ('package_path','runtime_path','tester_path','compile_script','execute_script'):
    shutil.copy2(ROOT/target[key],folder/Path(target[key]).name)
  if inject_failure:raise RuntimeError('injected staging failure')
  tmp.replace(dest);return value
 except Exception:
  shutil.rmtree(tmp,ignore_errors=True);raise
