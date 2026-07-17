[CmdletBinding()]param([Parameter(Mandatory=$true)][string]$LaunchId,[Parameter(Mandatory=$true)][string]$CampaignId,[Parameter(Mandatory=$true)][string]$CampaignToolPath,[Parameter(Mandatory=$true)][string]$CampaignToolSha256,[Parameter(Mandatory=$true)][string]$RepositoryCommit,[Parameter(Mandatory=$true)][string]$CaptureToolPath,[Parameter(Mandatory=$true)][string]$CaptureToolSha256,[Parameter(Mandatory=$true)][string]$RunnerPath,[Parameter(Mandatory=$true)][string]$RunnerSha256,[Parameter(Mandatory=$true)][string]$WrapperPath,[Parameter(Mandatory=$true)][string]$WrapperSha256,[string]$EvidenceRoot='C:\NoraEvidence\Phase2',[int]$CaptureCount=20)
Set-StrictMode -Version Latest;$ErrorActionPreference='Stop'
function Hash($p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
function Atomic($p,$v){$t=$p+'.partial.'+[guid]::NewGuid().ToString('N');[IO.File]::WriteAllText($t,($v|ConvertTo-Json -Depth 20 -Compress),[Text.UTF8Encoding]::new($false));if(Test-Path $p){throw 'immutable launch artifact exists'};[IO.File]::Move($t,$p)}
foreach($id in @($LaunchId,$CampaignId)){if($id-notmatch'^[A-Za-z0-9][A-Za-z0-9._-]{7,127}$'){throw 'invalid launch or campaign id'}}
if((Hash $CampaignToolPath)-ne$CampaignToolSha256 -or (Hash $CaptureToolPath)-ne$CaptureToolSha256 -or (Hash $RunnerPath)-ne$RunnerSha256 -or (Hash $WrapperPath)-ne$WrapperSha256){throw 'deployed identity mismatch'}
$root=Join-Path (Join-Path $EvidenceRoot 'firewall-launches') $LaunchId
if(Test-Path $root){throw 'duplicate launch id'}
if(Test-Path (Join-Path (Join-Path $EvidenceRoot 'firewall-campaigns') $CampaignId)){throw 'duplicate campaign id'}
New-Item -ItemType Directory -Path $root -ErrorAction Stop|Out-Null
$out=Join-Path $root 'stdout.txt'
$err=Join-Path $root 'stderr.txt'
$payload=[ordered]@{
  schema_version='nora.phase2_firewall_launch_payload_v1'
  launch_id=$LaunchId;campaign_id=$CampaignId;evidence_root=$EvidenceRoot
  campaign_tool_path=$CampaignToolPath;campaign_tool_sha256=$CampaignToolSha256
  runner_path=$RunnerPath;runner_sha256=$RunnerSha256
  capture_tool_path=$CaptureToolPath;capture_tool_sha256=$CaptureToolSha256
  wrapper_path=$WrapperPath;wrapper_sha256=$WrapperSha256
  repository_commit=$RepositoryCommit;capture_count=$CaptureCount
  stdout_path=$out;stderr_path=$err
}
$logical=($payload|ConvertTo-Json -Compress)
$payload.logical_command_sha256=([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($logical)))).Replace('-','').ToLowerInvariant()
$encodedForSubmission=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes(($payload|ConvertTo-Json -Compress)))
$command='powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File '+$WrapperPath+' -PayloadBase64 '+$encodedForSubmission
$submitted=([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($command)))).Replace('-','').ToLowerInvariant()
$payload.submitted_command_sha256=$submitted
$encoded=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes(($payload|ConvertTo-Json -Compress)))
$intent=[ordered]@{
  schema_version='nora.phase2_firewall_campaign_launch_v2'
  launch_id=$LaunchId;campaign_id=$CampaignId;payload=$payload;encoded_payload=$encoded
  logical_command_sha256=$payload.logical_command_sha256;submitted_command=$command
  submitted_command_sha256=$submitted;requested_utc=(Get-Date).ToUniversalTime().ToString('o')
}
Atomic (Join-Path $root 'intent.json') $intent
$procArgs=@('-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',$WrapperPath,'-PayloadBase64',$encoded)
$proc=Start-Process -FilePath powershell.exe -ArgumentList $procArgs -PassThru
$created=[pscustomobject]@{ReturnValue=0;ProcessId=$proc.Id}
if(!$created.ProcessId){
  Atomic (Join-Path $root 'failure.json') ([ordered]@{launch_id=$LaunchId;reason='PROCESS_CREATE_FAILED';return_value=1;pid=$null})
  throw 'process creation failure'
}
$campaignPid=$null
for($i=0;$i-lt600;$i++){
  Start-Sleep -Milliseconds 50
  $outcome=Join-Path $root 'wrapper-outcome.json'
  if(Test-Path $outcome){
    $wo=Get-Content $outcome -Raw|ConvertFrom-Json
    $campaignPid=$wo.campaign_pid
    break
  }
}
if(!$campaignPid){
  Atomic (Join-Path $root 'failure.json') ([ordered]@{launch_id=$LaunchId;campaign_id=$CampaignId;reason='WRAPPER_OUTCOME_MISSING';pid=$created.ProcessId;stdout_path=$out;stderr_path=$err})
  throw 'wrapper outcome missing'
}
$owner=Join-Path (Join-Path (Join-Path $EvidenceRoot 'firewall-campaigns') $CampaignId) 'owner.json'
$view=$null
for($i=0;$i-lt100;$i++){
  Start-Sleep -Milliseconds 100
  if(Test-Path $owner){
    $o=Get-Content $owner -Raw|ConvertFrom-Json
    if($o.launch_id -eq $LaunchId -and $o.owner_pid -eq $campaignPid){
      $view=Get-CimInstance Win32_Process -Filter ('ProcessId='+$campaignPid)
      break
    }
  }
  if(!(Get-Process -Id $campaignPid -ErrorAction SilentlyContinue)){break}
}
if(!$view){
  Atomic (Join-Path $root 'failure.json') ([ordered]@{launch_id=$LaunchId;campaign_id=$CampaignId;reason='bootstrap_not_acknowledged';pid=$created.ProcessId;stdout_path=$out;stderr_path=$err})
  throw 'campaign bootstrap not acknowledged'
}
$intent=Get-Content (Join-Path $root 'intent.json') -Raw|ConvertFrom-Json
$o=Get-Content $owner -Raw|ConvertFrom-Json
$wrapperStart=Get-Content (Join-Path $root 'wrapper-start.json') -Raw|ConvertFrom-Json
if($intent.payload.submitted_command_sha256 -ne $payload.submitted_command_sha256 -or $o.submitted_command_sha256 -ne $payload.submitted_command_sha256 -or $wrapperStart.submitted_command_sha256 -ne $payload.submitted_command_sha256){throw 'submitted command identity mismatch'}
Atomic (Join-Path $root 'receipt.json') ([ordered]@{
  schema_version='nora.phase2_firewall_campaign_launch_receipt_v2'
  launch_id=$LaunchId;campaign_id=$CampaignId;intent_sha256=Hash (Join-Path $root 'intent.json')
  wrapper_process=[ordered]@{pid=[int]$wrapperStart.wrapper_process.pid;creation_time_utc=[string]$wrapperStart.wrapper_process.creation_time_utc;executable_path=[string]$wrapperStart.wrapper_process.executable_path;command_line=[string]$wrapperStart.wrapper_process.command_line;windows_user=[string]$wrapperStart.wrapper_process.windows_user;user_sid=[string]$wrapperStart.wrapper_process.user_sid}
  campaign_process=[ordered]@{pid=[int]$o.campaign_process.pid;creation_time_utc=[string]$o.campaign_process.creation_time_utc;executable_path=[string]$o.campaign_process.executable_path;command_line=[string]$o.campaign_process.command_line;windows_user=[string]$o.campaign_process.windows_user;user_sid=[string]$o.campaign_process.user_sid}
  submitted_command_sha256=$payload.submitted_command_sha256
  owner_path=$owner;owner_sha256=Hash $owner;stdout_path=$out;stderr_path=$err
  acknowledged_utc=(Get-Date).ToUniversalTime().ToString('o')
})
Get-Content (Join-Path $root 'receipt.json') -Raw