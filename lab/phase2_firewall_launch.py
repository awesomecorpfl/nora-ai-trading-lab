"""Canonical, shell-free payload and process-binding contracts for Phase 2."""
from __future__ import annotations
import base64, hashlib, json, re
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{7,127}$")
HEX = re.compile(r"^[0-9a-f]{64}$")
class LaunchError(ValueError): pass
def canonical(v): return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
def sha(v): return hashlib.sha256(canonical(v)).hexdigest()
def _hash(v, name):
    if not isinstance(v, str) or not HEX.fullmatch(v) or v == "unavailable": raise LaunchError(f"{name} unavailable")
def build(**v):
    required=('launch_id','campaign_id','evidence_root','campaign_tool_path','campaign_tool_sha256','runner_path','runner_sha256','capture_tool_path','capture_tool_sha256','wrapper_path','wrapper_sha256','repository_commit','capture_count','stdout_path','stderr_path')
    if set(required)-set(v): raise LaunchError('missing launch field')
    if not ID.fullmatch(v['launch_id']) or not ID.fullmatch(v['campaign_id']): raise LaunchError('identity')
    if not re.fullmatch(r'[0-9a-f]{40}',v['repository_commit']): raise LaunchError('commit')
    if not isinstance(v['capture_count'],int) or v['capture_count']<1: raise LaunchError('count')
    for k in required:
        if k.endswith('_sha256'): _hash(v[k], k)
        if k.endswith('_path') and (not isinstance(v[k],str) or not v[k]): raise LaunchError('path')
    x={k:v[k] for k in required}; x['schema_version']='nora.phase2_firewall_launch_payload_v1'; x['logical_command_sha256']=sha(x)
    raw=canonical(x); x['encoded_payload']=base64.b64encode(raw).decode('ascii')
    x['submitted_command_sha256']=hashlib.sha256(('powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File '+x['wrapper_path']+' -PayloadBase64 '+x['encoded_payload']).encode('utf-8')).hexdigest()
    return x
def validate_process_binding(receipt: dict, wrapper_start: dict, owner: dict, intent: dict) -> dict:
    if receipt.get('schema_version') != 'nora.phase2_firewall_campaign_launch_receipt_v2': raise LaunchError('receipt schema')
    wp, cp = receipt.get('wrapper_process'), receipt.get('campaign_process')
    sw, co = wrapper_start.get('wrapper_process'), owner.get('campaign_process')
    if not isinstance(wp, dict) or not isinstance(cp, dict) or not isinstance(sw, dict) or not isinstance(co, dict): raise LaunchError('process identities incomplete')
    for name, obj in (('wrapper', wp), ('campaign', cp), ('wrapper_start', sw), ('campaign_owner', co)):
        for field in ('pid','creation_time_utc','executable_path','command_line','windows_user','user_sid'):
            if not obj.get(field): raise LaunchError(f'{name} process field missing: {field}')
    for field in ('pid','creation_time_utc','executable_path','command_line','windows_user','user_sid'):
        if wp[field] != sw[field]: raise LaunchError(f'wrapper process mismatch: {field}')
        if cp[field] != co[field]: raise LaunchError(f'campaign process mismatch: {field}')
    if wp['pid'] == cp['pid']: raise LaunchError('wrapper and campaign process are not distinct')
    hashes=[intent.get('payload',{}).get('submitted_command_sha256'), wrapper_start.get('submitted_command_sha256'), owner.get('submitted_command_sha256'), receipt.get('submitted_command_sha256')]
    if any(not isinstance(x,str) or not HEX.fullmatch(x) or x == 'unavailable' for x in hashes): raise LaunchError('submitted command hash unavailable')
    if len(set(hashes)) != 1: raise LaunchError('submitted command hash mismatch')
    return {'verdict':'PASS','wrapper_pid':wp['pid'],'campaign_pid':cp['pid'],'submitted_command_sha256':hashes[0]}
