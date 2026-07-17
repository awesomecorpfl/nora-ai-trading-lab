import pytest
from lab.phase2_firewall_launch import build,LaunchError
def x(**k):
 d=dict(launch_id='launch-0001',campaign_id='campaign-0001',evidence_root='C:\\NoraEvidence\\Phase2',campaign_tool_path='C:\\x a.ps1',campaign_tool_sha256='a'*64,runner_path='C:\\r',runner_sha256='b'*64,capture_tool_path='C:\\c',capture_tool_sha256='c'*64,wrapper_path='C:\\w',wrapper_sha256='d'*64,repository_commit='e'*40,capture_count=20,stdout_path='C:\\o',stderr_path='C:\\e');d.update(k);return build(**d)
def test_canonical_stable_and_metacharacters():assert x(campaign_tool_path="C:\\x $;&|' ü.ps1")==x(campaign_tool_path="C:\\x $;&|' ü.ps1")
@pytest.mark.parametrize('k,v',[('launch_id','x'),('capture_count',0),('runner_sha256','bad'),('stdout_path','')])
def test_rejects_bad_contract(k,v):
 with pytest.raises(LaunchError):x(**{k:v})

def test_wrapper_has_explicit_owner_binding_mismatch_classifier():
 script=(__import__('pathlib').Path(__file__).parents[1]/'phase-0a-h/windows/phase2-firewall-launch-wrapper.ps1').read_text()
 for token in ('OWNER_BINDING_MISMATCH','owner-binding-mismatch.json','parent_process_id','mismatch_fields','success_receipt_present','claims_count'):
  assert token in script
