import hashlib,json,threading
from pathlib import Path
import pytest
from lab.phase2_firewall_campaign import CampaignError,verify

ROOT=Path(__file__).parents[1]
SCRIPT=(ROOT/'phase-0a-h/windows/phase2-firewall-campaign.ps1').read_text()
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,separators=(',',':')))
def campaign(tmp,n=2):
 root=tmp/'campaign';root.mkdir();owner={'schema_version':'nora.phase2_firewall_campaign_v1','campaign_id':'campaign-0001','capture_tool_sha256':'a'*64,'repository_commit':'b'*40};put(root/'owner.json',owner)
 for i in range(1,n+1):
  final=root/'captures'/f'{i:02d}.json';final.parent.mkdir(exist_ok=True);final.write_bytes(f'inventory-{i}'.encode())
  claim=root/'claims'/f'{i:02d}.json';put(claim,{'campaign_id':owner['campaign_id']})
  receipt={'campaign_id':owner['campaign_id'],'slot':i,'claim_sha256':h(claim),'owner_sha256':h(root/'owner.json'),'final_path':str(final),'final_sha256':h(final),'final_size':final.stat().st_size,'capture_tool_sha256':'a'*64,'repository_commit':'b'*40};put(root/'receipts'/f'{i:02d}.json',receipt)
 put(root/'completion.json',{'campaign_id':owner['campaign_id'],'owner_sha256':h(root/'owner.json'),'expected_capture_count':n,'capture_tool_sha256':'a'*64})
 (root/'partials').mkdir();return root
def test_campaign_verifier_accepts_one_owner_ordered_slots(tmp_path):assert verify(campaign(tmp_path),2)['verdict']=='PASS'
@pytest.mark.parametrize('mutator',[lambda r:(r/'captures'/'01.json').write_bytes(b'x'),lambda r:(r/'receipts'/'02.json').unlink(),lambda r:put(r/'receipts'/'02.json',{**json.loads((r/'receipts'/'02.json').read_text()),'slot':1}),lambda r:(r/'partials'/'x.partial').write_text('x')])
def test_campaign_verifier_rejects_tamper_missing_reordered_and_partial(tmp_path,mutator):
 r=campaign(tmp_path);mutator(r)
 with pytest.raises(CampaignError):verify(r,2)
def test_atomic_directory_claim_has_one_winner(tmp_path):
 target=tmp_path/'claim';out=[];barrier=threading.Barrier(2)
 def f():
  barrier.wait()
  try:target.mkdir();out.append('winner')
  except FileExistsError:out.append('loser')
 ts=[threading.Thread(target=f) for _ in range(2)]
 [t.start() for t in ts];[t.join() for t in ts]
 assert sorted(out)==['loser','winner']
def test_campaign_script_requires_atomic_owner_slot_and_nonoverwrite_publication():
 for token in ('New-Item -ItemType Directory -Path (Root) -ErrorAction Stop','AtomicJson (OwnerPath)','AtomicJson (ClaimPath $Number)','final capture overwrite attempt','[IO.File]::Move($temporary,(FinalPath $Number))','unresolved campaign partial','foreign campaign owner','completed immutable campaign cannot be resumed'):
  assert token in SCRIPT
 assert 'Remove-NetFirewallRule' not in SCRIPT and 'Set-NetFirewallRule' not in SCRIPT
def test_foreign_owner_and_mixed_identity_rejected(tmp_path):
 r=campaign(tmp_path);v=json.loads((r/'receipts'/'01.json').read_text());v['owner_sha256']='0'*64;put(r/'receipts'/'01.json',v)
 with pytest.raises(CampaignError,match='substitution'):verify(r,2)
