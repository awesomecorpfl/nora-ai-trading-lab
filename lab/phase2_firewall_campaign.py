"""Immutable Phase-2 firewall capture campaign ownership verification."""
from __future__ import annotations
import hashlib,json,re
from pathlib import Path
ID=re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{7,127}$"); HEX=re.compile(r"^[0-9a-f]{64}$")
class CampaignError(ValueError): pass
def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path:Path)->dict:
 try:return json.loads(path.read_bytes())
 except (OSError,json.JSONDecodeError) as e:raise CampaignError(f"invalid json: {path}") from e
def _slot_path(value, root:Path, folder:str, slot:int)->bool:
 s=str(value or '').replace('\\','/')
 return s == str(root/folder/f'{slot:02d}.json') or s.endswith(f'/{folder}/{slot:02d}.json')
def verify(root:Path, expected_count:int=20)->dict:
 root=Path(root); owner_path=root/'owner.json'; completion_path=root/'completion.json'; owner=load(owner_path); cid=owner.get('campaign_id')
 if not ID.fullmatch(str(cid or '')):raise CampaignError('invalid campaign id')
 if owner.get('schema_version')!='nora.phase2_firewall_campaign_v1':raise CampaignError('owner schema')
 if not HEX.fullmatch(str(owner.get('capture_tool_sha256',''))) or owner.get('capture_tool_sha256')=='unavailable':raise CampaignError('owner capture identity')
 if not HEX.fullmatch(str(owner.get('submitted_command_sha256',''))) or owner.get('submitted_command_sha256')=='unavailable':raise CampaignError('owner submitted identity')
 cp=owner.get('campaign_process')
 if not isinstance(cp,dict) or any(not cp.get(k) for k in ('pid','creation_time_utc','executable_path','command_line','windows_user','user_sid')):raise CampaignError('campaign process identity')
 receipts=[]; paths=[]; slots=[]
 for slot in range(1,expected_count+1):
  name=f'{slot:02d}.json';claim=root/'claims'/name;receipt_path=root/'receipts'/name;final=root/'captures'/name
  if not claim.is_file() or not receipt_path.is_file() or not final.is_file():raise CampaignError(f'missing slot {slot}')
  claim_v=load(claim);r=load(receipt_path)
  if claim_v.get('campaign_id')!=cid or r.get('campaign_id')!=cid or r.get('slot')!=slot:raise CampaignError('foreign or reordered slot')
  if r.get('claim_sha256')!=sha(claim) or r.get('owner_sha256')!=sha(owner_path):raise CampaignError('claim or owner substitution')
  if not _slot_path(r.get('final_path'),root/'captures','captures',slot) or r.get('final_sha256')!=sha(final) or r.get('final_size')!=final.stat().st_size:raise CampaignError('final artifact substitution')
  if r.get('capture_tool_sha256')!=owner.get('capture_tool_sha256') or r.get('repository_commit')!=owner.get('repository_commit'):raise CampaignError('mixed identity')
  receipts.append(r);paths.append(str(final));slots.append(slot)
 if len(set(paths))!=expected_count or slots!=list(range(1,expected_count+1)):raise CampaignError('slot uniqueness or order')
 if any((root/'partials').glob('*')):raise CampaignError('unresolved partial')
 done=load(completion_path)
 if done.get('campaign_id')!=cid or done.get('owner_sha256')!=sha(owner_path) or done.get('expected_capture_count')!=expected_count:raise CampaignError('completion identity')
 if done.get('capture_tool_sha256')!=owner.get('capture_tool_sha256'):raise CampaignError('completion capture identity')
 rp=done.get('receipt_paths');rh=done.get('receipt_sha256');cpth=done.get('capture_paths');ch=done.get('capture_sha256')
 if not all(isinstance(x,list) and len(x)==expected_count for x in (rp,rh,cpth,ch)):raise CampaignError('completion ordered bindings incomplete')
 assert isinstance(rp,list) and isinstance(rh,list) and isinstance(cpth,list) and isinstance(ch,list)
 for i in range(1,expected_count+1):
  if not _slot_path(rp[i-1],root/'receipts','receipts',i) or rp[i-1].replace('\\','/').endswith(f'/captures/{i:02d}.json'):raise CampaignError('capture path in receipt_paths')
  if rh[i-1]!=sha(root/'receipts'/f'{i:02d}.json'):raise CampaignError('receipt hash/path mismatch')
  if not _slot_path(cpth[i-1],root/'captures','captures',i) or ch[i-1]!=sha(root/'captures'/f'{i:02d}.json'):raise CampaignError('capture hash/path mismatch')
 return {'verdict':'PASS','campaign_id':cid,'owner_sha256':sha(owner_path),'completion_sha256':sha(completion_path),'slots':slots,'receipt_paths':rp,'capture_paths':cpth,'captures':[{'path':str(root/'captures'/f'{i:02d}.json'),'sha256':sha(root/'captures'/f'{i:02d}.json'),'size':(root/'captures'/f'{i:02d}.json').stat().st_size} for i in slots]}
