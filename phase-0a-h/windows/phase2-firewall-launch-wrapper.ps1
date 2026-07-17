[CmdletBinding()]param([Parameter(Mandatory=$true)][string]$PayloadBase64)
$ErrorActionPreference='Continue'
Set-StrictMode -Version Latest
$tl='C:\NoraEvidence\Phase2\wrapper-trap3.log'
if(Test-Path $tl){Remove-Item $tl -Force}
function TL([string]$m){[IO.File]::AppendAllText($tl,((Get-Date).ToString('HH:mm:ss.fff')+"`t"+$m+"`n"))}
TL('START pid='+$PID)
try{
Set-StrictMode -Version Latest;$ErrorActionPreference='Stop'
function Save-Artifact([Parameter(Mandatory=$true,Position=0)][string]$Path,[Parameter(Mandatory=$true,Position=1)][object]$Value){$t=$Path+'.partial.'+[guid]::NewGuid().ToString('N');[IO.File]::WriteAllText($t,($Value|ConvertTo-Json -Depth 20 -Compress),[Text.UTF8Encoding]::new($false));if(Test-Path $Path){throw 'immutable artifact exists'};[IO.File]::Move($t,$Path)}
function Get-SHA256([Parameter(Mandatory=$true,Position=0)][string]$LiteralPath){(Get-FileHash -LiteralPath $LiteralPath -Algorithm SHA256).Hash.ToLowerInvariant()}
$p=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($PayloadBase64))|ConvertFrom-Json
TL('decoded. has submitted_command_sha256: '+($p.PSObject.Properties.Name -contains 'submitted_command_sha256'))
TL('has logical_command_sha256: '+($p.PSObject.Properties.Name -contains 'logical_command_sha256'))
if($p.schema_version-ne'nora.phase2_firewall_launch_payload_v1'){TL('SCHEMA FAIL');throw 'payload schema'}
$root=Join-Path (Join-Path $p.evidence_root 'firewall-launches') $p.launch_id
$start=Join-Path $root 'wrapper-start.json'
$out=$p.stdout_path
$err=$p.stderr_path
New-Item -ItemType File -Path $out -Force|Out-Null
New-Item -ItemType File -Path $err -Force|Out-Null
$self=Get-CimInstance Win32_Process -Filter ('ProcessId='+$PID)
Save-Artifact $start ([ordered]@{schema_version='nora.phase2_firewall_wrapper_start_v1';launch_id=$p.launch_id;campaign_id=$p.campaign_id;wrapper_pid=$PID;wrapper_start_utc=([datetime]$self.CreationDate).ToUniversalTime().ToString('o');windows_user=[Security.Principal.WindowsIdentity]::GetCurrent().Name;wrapper_path=$PSCommandPath;wrapper_sha256=(Get-SHA256 $PSCommandPath);logical_command_sha256=$p.logical_command_sha256;submitted_command_sha256=$p.submitted_command_sha256;campaign_tool_sha256=$p.campaign_tool_sha256;runner_sha256=$p.runner_sha256;capture_tool_sha256=$p.capture_tool_sha256;repository_commit=$p.repository_commit;stdout_path=$out;stderr_path=$err})
TL('wrapper-start saved')
$procArgs=@('-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',$p.campaign_tool_path,'-Mode','run','-LaunchId',$p.launch_id,'-CampaignId',$p.campaign_id,'-RepositoryCommit',$p.repository_commit,'-CaptureToolPath',$p.capture_tool_path,'-CaptureToolSha256',$p.capture_tool_sha256,'-RunnerPath',$p.runner_path,'-RunnerSha256',$p.runner_sha256,'-WrapperPath',$p.wrapper_path,'-WrapperSha256',$p.wrapper_sha256,'-LogicalCommandSha256',$p.logical_command_sha256,'-SubmittedCommandSha256',$p.submitted_command_sha256,'-WrapperPid',[string]$PID,'-WrapperStartUtc',([datetime]$self.CreationDate).ToUniversalTime().ToString('o'),'-EvidenceRoot',$p.evidence_root,'-CaptureCount',[string]$p.capture_count)
TL('procArgs built, count='+$procArgs.Count)
$c=Start-Process -FilePath powershell.exe -ArgumentList $procArgs -RedirectStandardOutput $out -RedirectStandardError $err -PassThru
TL('campaign started pid='+$c.Id)
$cv=Get-CimInstance Win32_Process -Filter ('ProcessId='+$c.Id)
$owner=Join-Path (Join-Path (Join-Path $p.evidence_root 'firewall-campaigns') $p.campaign_id) 'owner.json'
for($i=0;$i-lt100;$i++){
  if(Test-Path $owner){
    $o=Get-Content $owner -Raw|ConvertFrom-Json
    if($o.launch_id-eq$p.launch_id -and $o.owner_pid-eq$c.Id){
      Save-Artifact (Join-Path $root 'wrapper-outcome.json') ([ordered]@{state='BOOTSTRAP_ACQUIRED';campaign_pid=$c.Id;campaign_start_utc=([datetime]$cv.CreationDate).ToUniversalTime().ToString('o');owner_path=$owner;owner_sha256=(Get-SHA256 $owner)})
      TL('BOOTSTRAP_ACQUIRED')
      exit 0
    }
  }
  if($c.HasExited){break}
  Start-Sleep -Milliseconds 100
}
$c.Refresh()
Save-Artifact (Join-Path $root 'wrapper-outcome.json') ([ordered]@{state=if($c.HasExited){'CAMPAIGN_EXITED_BEFORE_OWNER'}else{'BOOTSTRAP_TIMEOUT_PROCESS_ALIVE'};campaign_pid=$c.Id;exit_code=if($c.HasExited){$c.ExitCode}else{$null};stdout_sha256=(Get-SHA256 $out);stderr_sha256=(Get-SHA256 $err);owner_present=(Test-Path $owner)})
TL('outcome saved')
exit 1
}catch{
  TL('CATCH: '+$_.Exception.Message)
  TL('STACK: '+$_.ScriptStackTrace)
  exit 2
}