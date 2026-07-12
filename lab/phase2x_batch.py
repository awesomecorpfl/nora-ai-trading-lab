"""Frozen V2 local-only Phase-2X batch contract, preflight, and staging."""
from __future__ import annotations
import hashlib,json,shutil,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; MANIFEST='tests/fixtures/phase2x_native_batch_v2.json'; VERSION='nora.phase2x.native_batch_v2'
def canon(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def file_sha(path):return sha((ROOT/path).read_bytes())
def _vectors(identifier,evidence,package):
 e=json.loads((ROOT/evidence).read_text()); rows=list(range(e['row_count']))
 if identifier=='macd': fields=['row','close','macd_null','macd','signal_null','signal','histogram_null','histogram','pass']; data={'row':rows,'close':e['close'],'macd':e['macd'],'signal':e['signal'],'histogram':e['histogram_vector']}
 else: fields=['row','source','source_null','percentile','percentile_null','pass']; data={'row':rows,'source':e['input_vector'],'percentile':e['percentile_vector']}
 masks={k:[x is None for x in v] for k,v in data.items() if k not in ('row','close','source')};data['null_masks']=masks
 value={'target':identifier,'columns':fields,'rows':rows,'vectors':data,'row_count':e['row_count'],'csv_schema_version':'v2'};value['expected_vector_identity']=sha(canon(value));return value
def build_manifest():
 specs=(('macd','tests/fixtures/phase2u_macd/phase2u_macd_executable_package.json','tests/fixtures/phase2u_macd/phase2u_macd_executable_rust_evidence.json','tests/fixtures/phase2u_macd/NoraPhase2MacdRuntimeV2.mqh','tests/fixtures/phase2u_macd/NoraPhase2MacdTesterCanaryV2.mq5','phase-0a-h/windows/compile-macd-tester-canary.ps1','phase-0a-h/windows/execute-macd-tester-canary.ps1'),('percentile','tests/fixtures/phase2w_percentile/phase2w_percentile_executable_package.json','tests/fixtures/phase2w_percentile/phase2w_percentile_executable_rust_evidence.json','tests/fixtures/phase2w_percentile/NoraPhase2PercentileRuntimeV2.mqh','tests/fixtures/phase2w_percentile/NoraPhase2PercentileTesterCanaryV2.mq5','phase-0a-h/windows/compile-percentile-tester-canary.ps1','phase-0a-h/windows/execute-percentile-tester-canary.ps1'))
 targets=[]
 for ident,pkg,evidence,runtime,tester,compile_script,execute_script in specs:
  p=json.loads((ROOT/pkg).read_text());e=json.loads((ROOT/evidence).read_text()); files=[pkg,evidence,runtime,tester,compile_script,execute_script]
  targets.append({'id':ident,'version':p['version'],'rust_task_identity':e['task_semantic_identity'],'rust_component_identity':p.get('rust_macd_component_identity',p.get('rust_percentile_identity')),'runtime_identity':p['runtime_identity'],'tester_identity':p['tester_identity'],'package_identity':p['package_identity'],'expected_vectors':_vectors(ident,evidence,pkg),'result_filename':p['csv_filename'],'completion_marker':p['completion_marker'],'failure_marker':('NORA_PHASE2U_MACD_FAIL' if ident=='macd' else 'NORA_PHASE2W_PERCENTILE_FAIL'),'files':[{'path':x,'sha256':file_sha(x)} for x in files],'native_execution_attempted':False,'native_parity':False,'grammar_admitted':False,'searchable':False})
 value={'schema_version':VERSION,'historical_batch_identity':'97d223ac2e217da907094b07fcc77e8ae97b6c713380c1aa47bf5e475779b23f','target_order':['macd','percentile'],'targets':targets,'allowlisted_paths':[MANIFEST]+[f['path'] for t in targets for f in t['files']]};value['staged_inventory_identity']=sha(canon(value['allowlisted_paths']));value['batch_identity']=sha(canon(value));return value
def load():return json.loads((ROOT/MANIFEST).read_text())
def manifest():return load()
def preflight(report,manifest_path=MANIFEST,fail_publish=False):
 errors=[]
 try:v=json.loads((ROOT/manifest_path).read_text())
 except Exception as exc:v={};errors.append('manifest:'+str(exc))
 if v.get('schema_version')!=VERSION:errors.append('schema')
 ids=[t.get('id') for t in v.get('targets',[])];
 if len(ids)!=len(set(ids)) or ids!=['macd','percentile']:errors.append('target identifiers')
 paths=[]
 for t in v.get('targets',[]):
  if t.get('native_parity') or t.get('grammar_admitted') or t.get('searchable'):errors.append('state:'+str(t.get('id')))
  ev=t.get('expected_vectors',{});copy=dict(ev);identity=copy.pop('expected_vector_identity',None)
  if identity!=sha(canon(copy)):errors.append('vectors:'+str(t.get('id')))
  if ev.get('row_count')!=len(ev.get('rows',[])) or ev.get('rows')!=list(range(ev.get('row_count',-1))):errors.append('rows:'+str(t.get('id')))
  for f in t.get('files',[]):
   paths.append(f.get('path'));path=f.get('path','')
   if not (ROOT/path).is_file() or (ROOT/path).is_file() and file_sha(path)!=f.get('sha256'):errors.append('file:'+path)
  p=t.get('files',[{}])[0].get('path');
  try: package=json.loads((ROOT/p).read_text());
  except Exception: package={};errors.append('package:'+str(t.get('id')))
  for k in ('runtime_identity','tester_identity','package_identity'):
   if package.get(k)!=t.get(k):errors.append('identity:'+k+':'+str(t.get('id')))
 if len(paths)!=len(set(paths)):errors.append('duplicate paths')
 if set(v.get('allowlisted_paths',[]))!=set([manifest_path]+paths):errors.append('allowlist')
 report_value={'status':'PASS' if not errors else 'FAIL','batch_identity':v.get('batch_identity'),'errors':errors};out=Path(report);out.parent.mkdir(parents=True,exist_ok=True);tmp=out.with_suffix('.tmp')
 try:
  tmp.write_bytes(canon(report_value)+b'\n')
  if fail_publish:raise RuntimeError('injected report failure')
  tmp.replace(out)
 except Exception:tmp.unlink(missing_ok=True);raise
 return report_value
def stage(destination,manifest_path=MANIFEST,inject_failure=False):
 dest=Path(destination)
 if dest.exists():raise ValueError('existing destination')
 v=load() if manifest_path==MANIFEST else json.loads((ROOT/manifest_path).read_text());pre=preflight(dest.parent/'.preflight.json',manifest_path)
 if pre['status']!='PASS':raise ValueError('preflight')
 tmp=Path(tempfile.mkdtemp(prefix='.phase2xv2-',dir=dest.parent))
 try:
  for path in v['allowlisted_paths']:
   target=tmp/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/path,target)
  if inject_failure:raise RuntimeError('injected staging failure')
  tmp.replace(dest);return {'batch_identity':v['batch_identity'],'staged_inventory_identity':v['staged_inventory_identity']}
 except Exception:shutil.rmtree(tmp,ignore_errors=True);raise
