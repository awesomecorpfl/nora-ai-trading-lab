"""Fixed-vector Phase-2Y synthetic return reconciliation."""
import hashlib,json,math
from pathlib import Path
from pathlib import Path
from .phase2x_batch import canon,load
VERSION='nora.phase2y.reconcile_v2';TOL='abs(actual-expected) <= 1e-12 + 1e-9*abs(expected)'
def reconcile(value):
 b=load();errors=[];targets=[]
 if value.get('batch_identity')!=b['batch_identity']:return {'protocol_version':VERSION,'classification':'FAIL_IDENTITY','failure_reasons':['batch identity'],'native_parity_updated':False}
 for t in b['targets']:
  r=value.get('targets',{}).get(t['id']);cls='PASS_EXACT';reasons=[];maxima={}
  if not r:cls='FAIL_INCOMPLETE';reasons=['missing target']
  elif any(r.get(k)!=t[k] for k in ('rust_component_identity','runtime_identity','tester_identity','package_identity')) or r.get('expected_vector_identity')!=t['expected_vectors']['expected_vector_identity']:cls='FAIL_IDENTITY';reasons=['target identity']
  elif r.get('compile')!='compiled':cls='FAIL_COMPILE';reasons=['compile']
  elif r.get('runtime')=='interrupted':cls='FAIL_INTERRUPTED';reasons=['interrupted']
  elif r.get('runtime')!='completed' or r.get('completion_marker')!=t['completion_marker']:cls='FAIL_RUNTIME';reasons=['runtime or marker']
  else:
   ev=t['expected_vectors'];rows=r.get('rows',[])
   if len(rows)!=ev['row_count'] or [x.get('row') for x in rows]!=ev['rows']:cls='FAIL_ROW_ALIGNMENT';reasons=['rows']
   else:
    fields=[x for x in ev['vectors'] if x not in ('row','close','source','null_masks')]
    for field in fields:
     expected=ev['vectors'][field];actual=[x.get(field) for x in rows]
     if [x is None for x in actual]!=ev['vectors']['null_masks'][field]:cls='FAIL_NULL_ALIGNMENT';reasons.append(field+' null');break
     stats=[]
     for i,(a,e) in enumerate(zip(actual,expected)):
      if e is None:continue
      if not isinstance(a,(int,float)) or not math.isfinite(a):cls='FAIL_CONTRACT';reasons.append(field+' nonfinite');break
      ae=abs(a-e);re=ae/max(abs(e),1e-15);stats.append((ae,re,i,e,a))
      if ae!=0 and cls=='PASS_EXACT':cls='PASS_WITHIN_TOLERANCE'
      if ae>1e-12+1e-9*abs(e):cls='FAIL_VALUE_MISMATCH';reasons.append(field+' tolerance')
     if stats:maxima[field]={'maximum_absolute':max(stats),'maximum_relative':max(stats,key=lambda x:x[1])}
     if cls.startswith('FAIL_'):break
  targets.append({'id':t['id'],'classification':cls,'maxima':maxima,'failure_reasons':reasons})
 overall=next((x['classification'] for x in targets if x['classification'].startswith('FAIL_')),'PASS_WITHIN_TOLERANCE' if any(x['classification']=='PASS_WITHIN_TOLERANCE' for x in targets) else 'PASS_EXACT')
 out={'protocol_version':VERSION,'batch_identity':b['batch_identity'],'classification':overall,'targets':targets,'numeric_policy':{'formula':TOL,'relative_denominator':'max(abs(expected), 1e-15)'},'native_parity_updated':False};out['returned_result_identity']=hashlib.sha256(canon(value)).hexdigest();return out
def publish(value,destination,fail_publish=False):
 """Atomically publish immutable synthetic reconciliation evidence."""
 out=Path(destination)
 if out.exists():raise ValueError('existing reconciliation evidence')
 evidence=reconcile(value);tmp=out.with_suffix('.tmp')
 try:
  tmp.write_bytes(canon(evidence)+b'\n')
  if fail_publish:raise RuntimeError('injected reconciliation publication failure')
  tmp.replace(out)
 except Exception:tmp.unlink(missing_ok=True);raise
 return evidence
