"""Canonical, shell-free payload contract for the Phase-2 firewall launcher."""
from __future__ import annotations
import base64,hashlib,json,re
HEX=re.compile(r'^[0-9a-f]{64}$'); ID=re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]{7,127}$')
class LaunchError(ValueError): pass
def canonical(v): return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')
def sha(v): return hashlib.sha256(canonical(v)).hexdigest()
def build(**v):
 required=('launch_id','campaign_id','evidence_root','campaign_tool_path','campaign_tool_sha256','runner_path','runner_sha256','capture_tool_path','capture_tool_sha256','wrapper_path','wrapper_sha256','repository_commit','capture_count','stdout_path','stderr_path')
 if set(required)-set(v): raise LaunchError('missing launch field')
 if not ID.fullmatch(v['launch_id']) or not ID.fullmatch(v['campaign_id']):raise LaunchError('identity')
 if not re.fullmatch(r'[0-9a-f]{40}',v['repository_commit']):raise LaunchError('commit')
 if not isinstance(v['capture_count'],int) or v['capture_count']<1:raise LaunchError('count')
 for k in required:
  if k.endswith('_sha256') and not HEX.fullmatch(v[k]):raise LaunchError('hash')
  if k.endswith('_path') and (not isinstance(v[k],str) or not v[k]):raise LaunchError('path')
 x={k:v[k] for k in required};x['schema_version']='nora.phase2_firewall_launch_payload_v1';x['logical_command_sha256']=sha(x)
 raw=canonical(x);x['encoded_payload']=base64.b64encode(raw).decode('ascii');x['submitted_command_sha256']=hashlib.sha256(('powershell.exe -EncodedCommand '+x['encoded_payload']).encode('utf-8')).hexdigest();return x
