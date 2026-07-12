"""Versioned filesystem-return contract for synthetic Phase-2Y protocol tests."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
from .phase2x_batch import canon,load
VERSION='nora.phase2y.returned_package_v1'
def semantic(v):return hashlib.sha256(canon(v)).hexdigest()
def validate(manifest):
 b=load();errors=[]
 if manifest.get('schema_version')!=VERSION:errors.append('schema')
 if manifest.get('batch_identity')!=b['batch_identity']:errors.append('batch')
 targets=manifest.get('targets',[])
 if manifest.get('declared_target_count')!=len(targets):errors.append('target count')
 ids=[x.get('target_identifier') for x in targets]
 if len(ids)!=len(set(ids)):errors.append('duplicate target')
 expected={x['id']:x for x in b['targets']}
 for t in targets:
  target=expected.get(t.get('target_identifier'))
  if not target:errors.append('unknown target');continue
  for k in ('rust_task_identity','rust_component_identity','runtime_identity','tester_identity','package_identity'):
   if t.get(k)!=target.get(k):errors.append('identity:'+k)
  if t.get('expected_vector_identity')!=target['expected_vectors']['expected_vector_identity']:errors.append('vector identity')
  if t.get('expected_result_filename')!=target['result_filename']:errors.append('filename')
  for path in t.get('references',[]):
   if Path(path).is_absolute() or '..' in Path(path).parts:errors.append('path')
 if set(ids)!=set(expected):errors.append('missing target')
 return {'valid':not errors,'errors':errors,'returned_package_semantic_identity':semantic(manifest),'synthetic_protocol_fixture':True}
