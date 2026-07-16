"""Immutable Phase-2 firewall capture campaign ownership verification."""
from __future__ import annotations
import hashlib,json,re
from pathlib import Path

ID=re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{7,127}$")
HEX=re.compile(r"^[0-9a-f]{64}$")
class CampaignError(ValueError): pass
def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path:Path)->dict:
 try:return json.loads(path.read_bytes())
 except (OSError,json.JSONDecodeError) as e:raise CampaignError(f"invalid json: {path}") from e
def verify(root:Path, expected_count:int=20)->dict:
 root=Path(root); owner_path=root/'owner.json'; completion_path=root/'completion.json'
 owner=load(owner_path);cid=owner.get('campaign_id')
 if not ID.fullmatch(str(cid or '')):raise CampaignError('invalid campaign id')
 if owner.get('schema_version')!='nora.phase2_firewall_campaign_v1':raise CampaignError('owner schema')
 if not HEX.fullmatch(str(owner.get('capture_tool_sha256',''))):raise CampaignError('owner capture identity')
 receipts=[]; paths=[]; slots=[]
 for slot in range(1,expected_count+1):
  name=f'{slot:02d}.json';claim=root/'claims'/name;receipt_path=root/'receipts'/name;final=root/'captures'/name
  if not claim.is_file() or not receipt_path.is_file() or not final.is_file():raise CampaignError(f'missing slot {slot}')
  claim_v=load(claim);r=load(receipt_path)
  if claim_v.get('campaign_id')!=cid or r.get('campaign_id')!=cid or r.get('slot')!=slot:raise CampaignError('foreign or reordered slot')
  if r.get('claim_sha256')!=sha(claim) or r.get('owner_sha256')!=sha(owner_path):raise CampaignError('claim or owner substitution')
  if r.get('final_path')!=str(final) or r.get('final_sha256')!=sha(final) or r.get('final_size')!=final.stat().st_size:raise CampaignError('final artifact substitution')
  if r.get('capture_tool_sha256')!=owner.get('capture_tool_sha256') or r.get('repository_commit')!=owner.get('repository_commit'):raise CampaignError('mixed identity')
  receipts.append(r);paths.append(str(final));slots.append(slot)
 if len(set(paths))!=expected_count or slots!=list(range(1,expected_count+1)):raise CampaignError('slot uniqueness or order')
 if any((root/'partials').glob('*')):raise CampaignError('unresolved partial')
 done=load(completion_path)
 if done.get('campaign_id')!=cid or done.get('owner_sha256')!=sha(owner_path) or done.get('expected_capture_count')!=expected_count:raise CampaignError('completion identity')
 if done.get('capture_tool_sha256')!=owner.get('capture_tool_sha256'):raise CampaignError('completion capture identity')
 return {'verdict':'PASS','campaign_id':cid,'owner_sha256':sha(owner_path),'completion_sha256':sha(completion_path),'slots':slots,'captures':[{'path':str(root/'captures'/f'{i:02d}.json'),'sha256':sha(root/'captures'/f'{i:02d}.json'),'size':(root/'captures'/f'{i:02d}.json').stat().st_size} for i in slots]}
