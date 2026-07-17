import pytest
from lab.phase2_firewall_launch import build,LaunchError,validate_process_binding

def x(**k):
 d=dict(launch_id='launch-0001',campaign_id='campaign-0001',evidence_root='C:\\NoraEvidence\\Phase2',campaign_tool_path='C:\\x a.ps1',campaign_tool_sha256='a'*64,runner_path='C:\\r',runner_sha256='b'*64,capture_tool_path='C:\\c',capture_tool_sha256='c'*64,wrapper_path='C:\\w',wrapper_sha256='d'*64,repository_commit='e'*40,capture_count=20,stdout_path='C:\\o',stderr_path='C:\\e');d.update(k);return build(**d)
def test_canonical_stable_and_metacharacters():assert x(campaign_tool_path="C:\\x $;&|' ü.ps1")==x(campaign_tool_path="C:\\x $;&|' ü.ps1")
@pytest.mark.parametrize('k,v',[('launch_id','x'),('capture_count',0),('runner_sha256','bad'),('stdout_path','')])
def test_rejects_bad_contract(k,v):
 with pytest.raises(LaunchError):x(**{k:v})
def records():
 p=x();h=p['submitted_command_sha256'];wp={'pid':10,'creation_time_utc':'2026-01-01T00:00:00Z','executable_path':'powershell.exe','command_line':'wrapper command','windows_user':'user','user_sid':'S-1'};cp={'pid':20,'creation_time_utc':'2026-01-01T00:00:01Z','executable_path':'powershell.exe','command_line':'campaign command','windows_user':'user','user_sid':'S-1'}
 return p,{'payload':p}, {'schema_version':'nora.phase2_firewall_wrapper_start_v2','wrapper_process':wp,'submitted_command_sha256':h}, {'campaign_process':cp,'submitted_command_sha256':h}, {'schema_version':'nora.phase2_firewall_campaign_launch_receipt_v2','wrapper_process':wp.copy(),'campaign_process':cp.copy(),'submitted_command_sha256':h}
def test_process_identities_are_distinct_complete_and_hash_propagates():
 p,i,w,o,r=records();assert validate_process_binding(r,w,o,i)['verdict']=='PASS'
@pytest.mark.parametrize('side,field',[('wrapper_process','creation_time_utc'),('campaign_process','command_line'),('campaign_process','pid'),('wrapper_process','executable_path')])
def test_mixed_or_mismatched_process_identity_fails(side,field):
 p,i,w,o,r=records();r[side][field]='wrong'
 with pytest.raises(LaunchError):validate_process_binding(r,w,o,i)
def test_wrong_submitted_hash_fails_and_unavailable_is_rejected():
 p,i,w,o,r=records();r['submitted_command_sha256']='0'*64
 with pytest.raises(LaunchError):validate_process_binding(r,w,o,i)
 w['submitted_command_sha256']='unavailable'
 with pytest.raises(LaunchError):validate_process_binding(r,w,o,i)
def test_wrapper_contract_contains_explicit_binding_and_no_unavailable_fallback():
 from pathlib import Path
 s=(Path(__file__).parents[1]/'phase-0a-h/windows/phase2-firewall-launch-wrapper.ps1').read_text()
 for token in ('submitted command hash missing','submitted command hash mismatch','wrapper_process','nora.phase2_firewall_wrapper_start_v2','user_sid'):
  assert token in s
 assert "$submittedSha='unavailable'" not in s
def test_launcher_uses_bounded_thirty_second_ack_window():
 from pathlib import Path
 s=(Path(__file__).parents[1]/'phase-0a-h/windows/launch-phase2-firewall-campaign.ps1').read_text()
 assert 'for($i=0;$i-lt600;$i++)' in s
 assert 'Start-Process -FilePath powershell.exe' in s
 assert 'Invoke-CimMethod -ClassName Win32_Process' not in s
 assert '$p.submitted_command_sha256' not in s
 assert '$payload.submitted_command_sha256' in s
