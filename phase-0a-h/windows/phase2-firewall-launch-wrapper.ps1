[CmdletBinding()]param([Parameter(Mandatory=$true)][string]$PayloadBase64)
Set-StrictMode -Version Latest;$ErrorActionPreference='Stop'
function Save-Artifact([Parameter(Mandatory=$true,Position=0)][string]$Path,[Parameter(Mandatory=$true,Position=1)][object]$Value){$t=$Path+'.partial.'+[guid]::NewGuid().ToString('N');[IO.File]::WriteAllText($t,($Value|ConvertTo-Json -Depth 30 -Compress),[Text.UTF8Encoding]::new($false));if(Test-Path $Path){throw 'immutable artifact exists'};[IO.File]::Move($t,$Path)}
function Get-SHA256([Parameter(Mandatory=$true,Position=0)][string]$LiteralPath){(Get-FileHash -LiteralPath $LiteralPath -Algorithm SHA256).Hash.ToLowerInvariant()}
function Get-TextSHA256([Parameter(Mandatory=$true,Position=0)][string]$Text){$b=[Text.Encoding]::UTF8.GetBytes($Text);([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash($b))).Replace('-','').ToLowerInvariant()}
try{$p=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($PayloadBase64))|ConvertFrom-Json}catch{throw 'malformed launch payload'}
if($p.schema_version-ne'nora.phase2_firewall_launch_payload_v1'){throw 'payload schema'}
$root=Join-Path (Join-Path $p.evidence_root 'firewall-launches') $p.launch_id
$start=Join-Path $root 'wrapper-start.json';$out=$p.stdout_path;$err=$p.stderr_path
New-Item -ItemType File -Path $out -Force|Out-Null;New-Item -ItemType File -Path $err -Force|Out-Null
$self=Get-CimInstance Win32_Process -Filter ('ProcessId='+$PID)
$submittedSha=''
if(!$p.PSObject.Properties['submitted_command_sha256'] -or [string]::IsNullOrWhiteSpace([string]$p.submitted_command_sha256) -or [string]$p.submitted_command_sha256 -eq 'unavailable'){throw 'submitted command hash missing'}
$submittedSha=[string]$p.submitted_command_sha256
$hashPayload=[ordered]@{};foreach($prop in $p.PSObject.Properties){if($prop.Name-ne'submitted_command_sha256'){$hashPayload[$prop.Name]=$prop.Value}}
$hashEncoded=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes(($hashPayload|ConvertTo-Json -Compress)))
$hashCommand='powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File '+$p.wrapper_path+' -PayloadBase64 '+$hashEncoded
if((Get-TextSHA256 $hashCommand)-ne$submittedSha){throw 'submitted command hash mismatch'}
$logicalSha=''
if($p.PSObject.Properties['logical_command_sha256'] -and -not [string]::IsNullOrWhiteSpace([string]$p.logical_command_sha256)){$logicalSha=[string]$p.logical_command_sha256}
Save-Artifact $start ([ordered]@{schema_version='nora.phase2_firewall_wrapper_start_v2';launch_id=$p.launch_id;campaign_id=$p.campaign_id;wrapper_process=[ordered]@{pid=$PID;creation_time_utc=([datetime]$self.CreationDate).ToUniversalTime().ToString('o');executable_path=[string]$self.ExecutablePath;command_line=[string]$self.CommandLine;windows_user=[Security.Principal.WindowsIdentity]::GetCurrent().Name;user_sid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value};wrapper_path=$PSCommandPath;wrapper_sha256=(Get-SHA256 $PSCommandPath);logical_command_sha256=$logicalSha;submitted_command_sha256=$submittedSha;campaign_tool_sha256=$p.campaign_tool_sha256;runner_sha256=$p.runner_sha256;capture_tool_sha256=$p.capture_tool_sha256;repository_commit=$p.repository_commit;stdout_path=$out;stderr_path=$err})
$procArgs=@('-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',$p.campaign_tool_path,'-Mode','run','-LaunchId',$p.launch_id,'-CampaignId',$p.campaign_id,'-RepositoryCommit',$p.repository_commit,'-CaptureToolPath',$p.capture_tool_path,'-CaptureToolSha256',$p.capture_tool_sha256,'-RunnerPath',$p.runner_path,'-RunnerSha256',$p.runner_sha256,'-WrapperPath',$p.wrapper_path,'-WrapperSha256',$p.wrapper_sha256,'-LogicalCommandSha256',$logicalSha,'-SubmittedCommandSha256',$submittedSha,'-WrapperPid',[string]$PID,'-WrapperStartUtc',([datetime]$self.CreationDate).ToUniversalTime().ToString('o'),'-EvidenceRoot',$p.evidence_root,'-CaptureCount',[string]$p.capture_count)
$c=Start-Process -FilePath powershell.exe -ArgumentList $procArgs -RedirectStandardOutput $out -RedirectStandardError $err -PassThru
$cv=Get-CimInstance Win32_Process -Filter ('ProcessId='+$c.Id)
$owner=Join-Path (Join-Path (Join-Path $p.evidence_root 'firewall-campaigns') $p.campaign_id) 'owner.json'
for($i=0;$i-lt100;$i++){
  if(Test-Path $owner){
    $o=Get-Content $owner -Raw|ConvertFrom-Json
    $mismatchFields=@();$comparisons=@()
    $checks=@(
      [ordered]@{field='launch_id';claimed=[string]$o.launch_id;actual=[string]$p.launch_id},
      [ordered]@{field='owner_pid';claimed=[string]$o.owner_pid;actual=[string]$c.Id},
      [ordered]@{field='parent_process_id';claimed=[string]$o.parent_process_id;actual=[string]$cv.ParentProcessId},
      [ordered]@{field='wrapper_pid';claimed=[string]$o.wrapper_pid;actual=[string]$PID}
    )
    foreach($check in $checks){$equal=([string]::Equals($check.claimed,$check.actual,[StringComparison]::Ordinal));$comparisons+=([ordered]@{field=$check.field;claimed=$check.claimed;actual=$check.actual;equal=$equal});if(!$equal){$mismatchFields+=@($check.field)}}
    if($mismatchFields.Count -gt 0){
      $mismatchPath=Join-Path $root 'owner-binding-mismatch.json'
      Save-Artifact $mismatchPath ([ordered]@{schema_version='nora.phase2_firewall_owner_binding_mismatch_v1';classification='OWNER_BINDING_MISMATCH';launch_id=$p.launch_id;campaign_id=$p.campaign_id;owner_path=$owner;owner_sha256=(Get-SHA256 $owner);claimed_owner=[ordered]@{owner_pid=[string]$o.owner_pid;parent_process_id=[string]$o.parent_process_id;owner_process_start_utc=[string]$o.owner_process_start_utc;wrapper_pid=[string]$o.wrapper_pid;launch_id=[string]$o.launch_id};actual_process=[ordered]@{process_id=[string]$c.Id;parent_process_id=[string]$cv.ParentProcessId;creation_date=[string]$cv.CreationDate;command_line=[string]$cv.CommandLine;executable_path=[string]$cv.ExecutablePath};comparisons=$comparisons;mismatch_fields=$mismatchFields;verifier='phase2-firewall-launch-wrapper.ps1';success_receipt_path=(Join-Path $root 'receipt.json');success_receipt_present=(Test-Path (Join-Path $root 'receipt.json'));claims_path=(Join-Path (Join-Path (Join-Path $p.evidence_root 'firewall-campaigns') $p.campaign_id) 'claims');claims_count=@(Get-ChildItem (Join-Path (Join-Path (Join-Path $p.evidence_root 'firewall-campaigns') $p.campaign_id) 'claims') -File -ErrorAction SilentlyContinue).Count})
      Save-Artifact (Join-Path $root 'wrapper-outcome.json') ([ordered]@{state='OWNER_BINDING_MISMATCH';campaign_pid=$c.Id;owner_path=$owner;owner_sha256=(Get-SHA256 $owner);mismatch_path=$mismatchPath;mismatch_sha256=(Get-SHA256 $mismatchPath);success_receipt_present=(Test-Path (Join-Path $root 'receipt.json'));claims_count=@(Get-ChildItem (Join-Path (Join-Path (Join-Path $p.evidence_root 'firewall-campaigns') $p.campaign_id) 'claims') -File -ErrorAction SilentlyContinue).Count})
      exit 1
    }
    if($o.launch_id-eq$p.launch_id -and $o.owner_pid-eq$c.Id){Save-Artifact (Join-Path $root 'wrapper-outcome.json') ([ordered]@{state='BOOTSTRAP_ACQUIRED';campaign_pid=$c.Id;campaign_start_utc=([datetime]$cv.CreationDate).ToUniversalTime().ToString('o');owner_path=$owner;owner_sha256=(Get-SHA256 $owner)});exit 0}
  }
  if($c.HasExited){break};Start-Sleep -Milliseconds 100
}
$c.Refresh();Save-Artifact (Join-Path $root 'wrapper-outcome.json') ([ordered]@{state=if($c.HasExited){'CAMPAIGN_EXITED_BEFORE_OWNER'}else{'BOOTSTRAP_TIMEOUT_PROCESS_ALIVE'};campaign_pid=$c.Id;exit_code=if($c.HasExited){$c.ExitCode}else{$null};stdout_sha256=(Get-SHA256 $out);stderr_sha256=(Get-SHA256 $err);owner_present=(Test-Path $owner)});exit 1