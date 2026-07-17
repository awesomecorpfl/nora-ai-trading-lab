param(
 [Parameter(Mandatory=$true)][string]$RunId,
 [Parameter(Mandatory=$true)][string]$CaptureId,
 [string]$EvidenceRoot='C:\NoraEvidence\Phase2'
)
$ErrorActionPreference='Stop'
$schema='nora.phase2_incomplete_run_forensic_capture_v1'
if($RunId-notmatch'^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$'){throw 'invalid run identity'}
if($CaptureId-notmatch'^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$'){throw 'invalid capture identity'}

function Hash([string]$Path){(Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()}
function AtomicJson([string]$Path,$Value){$tmp=$Path+'.partial.'+[guid]::NewGuid().ToString('N');$Value|ConvertTo-Json -Depth 20 -Compress|Set-Content -LiteralPath $tmp -Encoding utf8 -NoNewline;[IO.File]::Move($tmp,$Path)}
function Identity(){ $i=[Security.Principal.WindowsIdentity]::GetCurrent();[ordered]@{name=$i.Name;sid=$i.User.Value} }
function ItemView([string]$Path,[string]$Base){
 $i=Get-Item -LiteralPath $Path -Force;$acl=Get-Acl -LiteralPath $Path
 [ordered]@{path=$Path;relative_path=if($Base){$Path.Substring($Base.Length).TrimStart('\').Replace('\','/')}else{$null};type=if($i.PSIsContainer){'directory'}else{'file'};attributes=[string]$i.Attributes;creation_utc=$i.CreationTimeUtc.ToString('o');last_write_utc=$i.LastWriteTimeUtc.ToString('o');last_access_utc=$i.LastAccessTimeUtc.ToString('o');owner=$acl.Owner;sddl=$acl.Sddl;size=if($i.PSIsContainer){$null}else{[int64]$i.Length};sha256=if($i.PSIsContainer){$null}else{Hash $Path}}
}
function TreeView([string]$Path){
 if([string]::IsNullOrWhiteSpace($Path) -or !(Test-Path -LiteralPath $Path)){return @()}
 $rootItem=ItemView $Path ''
 @(@($rootItem)+@(Get-ChildItem -LiteralPath $Path -Force -Recurse|Sort-Object FullName|ForEach-Object{ItemView $_.FullName $Path}))
}
function CopyEvidence([string]$Source,[string]$Destination){
 if([string]::IsNullOrWhiteSpace($Source) -or !(Test-Path -LiteralPath $Source)){return $false}
 $parent=Split-Path $Destination -Parent;if(!(Test-Path -LiteralPath $parent)){New-Item -ItemType Directory -Path $parent -Force|Out-Null}
 $item=Get-Item -LiteralPath $Source -Force
 if($item.PSIsContainer){New-Item -ItemType Directory -Path $Destination -Force|Out-Null;Copy-Item -LiteralPath (Join-Path $Source '*') -Destination $Destination -Recurse -Force}else{Copy-Item -LiteralPath $Source -Destination $Destination -Force}
 return $true
}
function EventCapture([string]$LogName,[datetime]$Start,[datetime]$End,[int[]]$Ids=@()){
 try{
  $info=Get-WinEvent -ListLog $LogName -ErrorAction Stop
  $filter=@{LogName=$LogName;StartTime=$Start;EndTime=$End};if($Ids.Count){$filter.Id=$Ids}
  $events=@(Get-WinEvent -FilterHashtable $filter -ErrorAction Stop|Sort-Object TimeCreated|ForEach-Object{[ordered]@{log_name=$_.LogName;record_id=$_.RecordId;id=$_.Id;level=[string]$_.LevelDisplayName;provider=$_.ProviderName;time_created_utc=$_.TimeCreated.ToUniversalTime().ToString('o');process_id=$_.ProcessId;thread_id=$_.ThreadId;user_id=if($_.UserId){$_.UserId.Value}else{$null};message=$_.Message;properties=@($_.Properties|ForEach-Object{$_.Value})}})
  [ordered]@{log_name=$LogName;enabled=$info.IsEnabled;record_count=$info.RecordCount;query_succeeded=$true;query_error=$null;events=$events}
 }catch{[ordered]@{log_name=$LogName;enabled=$null;record_count=$null;query_succeeded=$false;query_error=$_.Exception.Message;events=@()}}
}
function FirewallView(){
 $rules=@(Get-NetFirewallRule -ErrorAction Stop|Sort-Object Name|ForEach-Object{
  $r=$_;$apps=@(Get-NetFirewallApplicationFilter -AssociatedNetFirewallRule $r -ErrorAction SilentlyContinue);$addresses=@(Get-NetFirewallAddressFilter -AssociatedNetFirewallRule $r -ErrorAction SilentlyContinue);$ports=@(Get-NetFirewallPortFilter -AssociatedNetFirewallRule $r -ErrorAction SilentlyContinue);$services=@(Get-NetFirewallServiceFilter -AssociatedNetFirewallRule $r -ErrorAction SilentlyContinue)
  [ordered]@{name=$r.Name;instance_id=$r.InstanceID;display_name=$r.DisplayName;group=$r.Group;enabled=[string]$r.Enabled;direction=[string]$r.Direction;action=[string]$r.Action;profile=[string]$r.Profile;policy_store_source=$r.PolicyStoreSource;policy_store_source_type=[string]$r.PolicyStoreSourceType;primary_status=[string]$r.PrimaryStatus;status=[string]$r.Status;applications=@($apps|ForEach-Object{$_.Program});addresses=@($addresses|ForEach-Object{[ordered]@{local=$_.LocalAddress;remote=$_.RemoteAddress}});ports=@($ports|ForEach-Object{[ordered]@{protocol=$_.Protocol;local=$_.LocalPort;remote=$_.RemotePort}});services=@($services|ForEach-Object{$_.Service})}
 })
 $json=$rules|ConvertTo-Json -Depth 10 -Compress
 [ordered]@{rules=$rules;canonical_sha256=([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($json))).Replace('-','').ToLowerInvariant())}
}

$jobPath=Join-Path $EvidenceRoot ('jobs\'+$RunId+'.json')
if(!(Test-Path -LiteralPath $jobPath -PathType Leaf)){throw 'missing durable job record'}
$job=Get-Content -LiteralPath $jobPath -Raw|ConvertFrom-Json
if($job.run_identifier-ne$RunId){throw 'job identity mismatch'}
$captureRoot=Join-Path $EvidenceRoot ('forensics\'+$RunId)
$published=Join-Path $captureRoot ($CaptureId+'.published')
if(Test-Path -LiteralPath $published){Get-Content -LiteralPath (Join-Path $published 'manifest.json') -Raw;exit 0}
$partial=$published+'.partial.'+[guid]::NewGuid().ToString('N')
New-Item -ItemType Directory -Path $partial -Force|Out-Null

$sourcePaths=[ordered]@{
 run_directory=[string]$job.paths.running
 complete_directory=[string]$job.paths.complete
 job=$jobPath
 stdout=[string]$job.paths.stdout
 stderr=[string]$job.paths.stderr
 incoming=[string]$job.paths.incoming
 containment=[string]$job.containment_path
 deployed_runner=[string]$job.runner_script_path
 deployed_worker=[string]$job.worker_executable_path
}
$sourceInventory=[ordered]@{}
foreach($name in $sourcePaths.Keys){$sourceInventory[$name]=TreeView $sourcePaths[$name]}

$copies=[ordered]@{}
$copies.run_directory=CopyEvidence $sourcePaths.run_directory (Join-Path $partial 'source\run-directory')
$copies.job=CopyEvidence $sourcePaths.job (Join-Path $partial 'source\job.json')
$copies.stdout=CopyEvidence $sourcePaths.stdout (Join-Path $partial 'source\stdout.log')
$copies.stderr=CopyEvidence $sourcePaths.stderr (Join-Path $partial 'source\stderr.log')
$copies.incoming=CopyEvidence $sourcePaths.incoming (Join-Path $partial 'source\incoming')
$copies.containment=CopyEvidence $sourcePaths.containment (Join-Path $partial 'source\containment.json')
$copies.deployed_runner=CopyEvidence $sourcePaths.deployed_runner (Join-Path $partial 'source\deployed-runner.ps1')
$copies.deployed_worker=CopyEvidence $sourcePaths.deployed_worker (Join-Path $partial 'source\deployed-worker.ps1')

$created=[datetime]$job.created_utc;$start=$created.AddMinutes(-10);$end=([datetime]$job.updated_utc).AddMinutes(10)
$eventLogs=@(
 (EventCapture 'Windows PowerShell' $start $end)
 (EventCapture 'Microsoft-Windows-PowerShell/Operational' $start $end)
 (EventCapture 'OpenSSH/Operational' $start $end)
 (EventCapture 'Security' $start $end @(4688,4689))
 (EventCapture 'System' $start $end)
 (EventCapture 'Application' $start $end)
)
$processes=@(Get-CimInstance Win32_Process|Where-Object{$_.Name-match'(?i)^(powershell|pwsh|sshd|terminal64|metatester64|conhost)\.exe$'}|Sort-Object ProcessId|ForEach-Object{[ordered]@{name=$_.Name;pid=[int]$_.ProcessId;parent_pid=[int]$_.ParentProcessId;creation_utc=if($_.CreationDate){([datetime]$_.CreationDate).ToUniversalTime().ToString('o')}else{$null};executable_path=$_.ExecutablePath;command_line=$_.CommandLine;session_id=$_.SessionId}})
$services=@(Get-CimInstance Win32_Service|Where-Object{$_.Name-in@('sshd','MpsSvc','EventLog','Winmgmt')}|Sort-Object Name|ForEach-Object{[ordered]@{name=$_.Name;state=$_.State;status=$_.Status;start_mode=$_.StartMode;process_id=$_.ProcessId;path_name=$_.PathName;start_name=$_.StartName}})
$firewall=FirewallView
$policy=@(Get-ExecutionPolicy -List|ForEach-Object{[ordered]@{scope=[string]$_.Scope;execution_policy=[string]$_.ExecutionPolicy}})
$ps=[ordered]@{version=$PSVersionTable;executable=(Get-Process -Id $PID).Path;is_64_bit_process=[Environment]::Is64BitProcess;is_64_bit_os=[Environment]::Is64BitOperatingSystem;working_directory=(Get-Location).Path;execution_policy=$policy;identity=Identity;environment=@(Get-ChildItem Env:|Sort-Object Name|ForEach-Object{[ordered]@{name=$_.Name;value=$_.Value}})}
$diagnostics=[ordered]@{schema_version=$schema;run_identifier=$RunId;capture_identifier=$CaptureId;captured_utc=(Get-Date).ToUniversalTime().ToString('o');capture_tool_path=$PSCommandPath;capture_tool_sha256=Hash $PSCommandPath;source_paths=$sourcePaths;source_inventory=$sourceInventory;copies=$copies;durable_job=$job;powershell=$ps;processes=$processes;services=$services;firewall=$firewall;event_window_start_utc=$start.ToUniversalTime().ToString('o');event_window_end_utc=$end.ToUniversalTime().ToString('o');event_logs=$eventLogs}
AtomicJson (Join-Path $partial 'diagnostics.json') $diagnostics
$captureInventory=@(Get-ChildItem -LiteralPath $partial -File -Recurse|Sort-Object FullName|ForEach-Object{[ordered]@{path=$_.FullName.Substring($partial.Length).TrimStart('\').Replace('\','/');size=[int64]$_.Length;sha256=Hash $_.FullName}})
$manifest=[ordered]@{schema_version=$schema;run_identifier=$RunId;capture_identifier=$CaptureId;classification='forensic_capture_only_source_run_unmodified';source_run_state=[string]$job.state;capture_inventory=$captureInventory;diagnostics_sha256=Hash (Join-Path $partial 'diagnostics.json');completed_utc=(Get-Date).ToUniversalTime().ToString('o');windows_identity=Identity}
AtomicJson (Join-Path $partial 'manifest.json') $manifest
Move-Item -LiteralPath $partial -Destination $published
Get-Content -LiteralPath (Join-Path $published 'manifest.json') -Raw
