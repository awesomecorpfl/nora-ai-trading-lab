"""Fedora-only validation of returned Phase-2X native-result packages."""
from __future__ import annotations
import json,math
from pathlib import Path
from .phase2x_batch import manifest
CLASSES=('PASS_EXACT','PASS_WITHIN_TOLERANCE','FAIL_VALUE_MISMATCH','FAIL_NULL_ALIGNMENT','FAIL_ROW_ALIGNMENT','FAIL_COMPILE','FAIL_RUNTIME','FAIL_INTERRUPTED','FAIL_IDENTITY','FAIL_INCOMPLETE','FAIL_CONTRACT')
def reconcile(result_dir):
 root=Path(result_dir);batch=manifest();results=[];overall='PASS_EXACT'
 try: returned=json.loads((root/'result.json').read_text())
 except Exception:return {'classification':'FAIL_INCOMPLETE','synthetic_protocol_fixture':True,'targets':[]}
 if returned.get('batch_identity')!=batch['batch_identity']:return {'classification':'FAIL_IDENTITY','synthetic_protocol_fixture':True,'targets':[]}
 for target in batch['targets']:
  item=returned.get('targets',{}).get(target['id']);classification='PASS_EXACT';max_abs=max_rel=0.0
  if not item:classification='FAIL_INCOMPLETE'
  elif item.get('target_identity')!=target['package_identity']:classification='FAIL_IDENTITY'
  elif item.get('compile')!='compiled':classification='FAIL_COMPILE'
  elif item.get('runtime')=='interrupted':classification='FAIL_INTERRUPTED'
  elif item.get('runtime')!='completed':classification='FAIL_RUNTIME'
  elif item.get('completion_marker')!=target['completion_marker']:classification='FAIL_INCOMPLETE'
  elif not isinstance(item.get('rows'),list) or len(item['rows'])!=target['expected_vectors']['row_count']:classification='FAIL_ROW_ALIGNMENT'
  else:
   seen=set()
   for i,row in enumerate(item['rows']):
    if row.get('row')!=i or i in seen:classification='FAIL_ROW_ALIGNMENT';break
    seen.add(i)
    for value in row.get('values',[]):
     if value is not None and (not isinstance(value,(int,float)) or not math.isfinite(value)):classification='FAIL_CONTRACT';break
    if classification!='PASS_EXACT':break
  results.append({'id':target['id'],'classification':classification,'max_absolute_divergence':max_abs,'max_relative_divergence':max_rel})
  if classification!='PASS_EXACT':overall=classification
 return {'classification':overall,'synthetic_protocol_fixture':True,'batch_identity':batch['batch_identity'],'targets':results,'native_parity_updated':False}
