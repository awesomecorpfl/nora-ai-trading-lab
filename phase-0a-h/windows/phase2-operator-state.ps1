[CmdletBinding()]
param(
 [Parameter(Mandatory=$true)][ValidateSet('inventory')][string]$Mode,
 [Parameter(Mandatory=$true)][string]$EvidenceRoot,
 [string]$QualificationId
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'

# Read-only extraction of the repository-owned legacy decoder/reconciliation contract.
function Read-ReconciledJobFile([string]$Path){
 $raw=[IO.File]::ReadAllBytes($Path)
 $job=([Text.Encoding]::UTF8.GetString($raw).TrimStart([char]0xFEFF)|ConvertFrom-Json)
 $legacy=[ordered]@{}
 if($job.PSObject.Properties.Name -contains 'Keys' -or $job.PSObject.Properties.Name -contains 'Values'){
  if(!($job.PSObject.Properties.Name -contains 'Keys') -or !($job.PSObject.Properties.Name -contains 'Values')){throw 'legacy job key/value shape incomplete'}
  $keys=@($job.Keys);$values=@($job.Values);if($keys.Count-ne$values.Count){throw 'legacy job key/value count mismatch'}
  for($i=0;$i-lt$keys.Count;$i++){if([string]::IsNullOrWhiteSpace([string]$keys[$i]) -or $legacy.Contains($keys[$i])){throw 'legacy job key invalid or duplicated'};$legacy[[string]$keys[$i]]=$values[$i]}
 }
 foreach($name in @('run_identifier','state','preflight_kind','created_utc','updated_utc')){
  $top=$null;if($job.PSObject.Properties.Name -contains $name){$top=$job.$name};$nested=if($legacy.Contains($name)){$legacy[$name]}else{$null}
  $topJson=if($null-ne$top){$top|ConvertTo-Json -Depth 20 -Compress}else{$null};$nestedJson=if($null-ne$nested){$nested|ConvertTo-Json -Depth 20 -Compress}else{$null}
  if($null-ne$top -and $null-ne$nested -and $topJson-ne$nestedJson){throw ('legacy job contradictory field:'+ $name)}
  if($null-ne$top){$legacy[$name]=$top}
 }
 if(!$legacy.run_identifier -or !$legacy.state){throw 'normalized job identity/state missing'}
 [ordered]@{raw=$raw;job=$job;normalized=$legacy}
}
function Hash-Bytes([byte[]]$Bytes){([Security.Cryptography.SHA256]::Create().ComputeHash($Bytes)|ForEach-Object{$_.ToString('x2')})-join''}
function Read-Reconciliation([string]$Path,[string]$RunId,[byte[]]$Raw){
 if(!(Test-Path -LiteralPath $Path -PathType Leaf)){throw 'reconciliation record missing'}
 $record=Get-Content -LiteralPath $Path -Raw|ConvertFrom-Json
 if($record.schema_version-ne'nora.phase2_prelaunch_reconciliation_v1' -or $record.run_identifier-ne$RunId -or $record.classification-ne'ABANDONED_PRE_LAUNCH_NO_CONTAINMENT' -or [bool]$record.accepted){throw 'untrusted reconciliation record'}
 if($record.original_job_sha256-ne(Hash-Bytes $Raw)){throw 'reconciliation original job mismatch'}
 if($record.PSObject.Properties.Name -contains 'original_job_size' -and [int64]$record.original_job_size -ne [int64]$Raw.Length){throw 'reconciliation original job size mismatch'}
 return $record
}
function Read-ReconciliationBinding([string]$Directory,[string]$RunId){
 $recordPath=Join-Path $Directory 'reconciliation.json';$originalPath=Join-Path $Directory 'original-job.json'
 if(!(Test-Path -LiteralPath $originalPath -PathType Leaf)){throw 'reconciliation original job missing'}
 $raw=[IO.File]::ReadAllBytes($originalPath);$record=Read-Reconciliation $recordPath $RunId $raw
 [ordered]@{record=$record;original_path=$originalPath;original_raw=$raw;original_size=[int64]$raw.Length;original_sha256=Hash-Bytes $raw}
}
function Get-ReconciledJobInventory([string]$Root){
 $jobsRoot=Join-Path $Root 'jobs';$reconRoot=Join-Path $Root 'reconciliations'
 $activeStates=@('launch-requested','launched','bootstrap-confirmed','running','contained')
 $pendingStates=$activeStates+@('prepared')
 $terminalStates=@('completed','failed','interrupted','cancelled','abandoned','packaging','published','accepted','rejected')
 $rows=@();$known=@{}
 if(Test-Path -LiteralPath $jobsRoot -PathType Container){
  foreach($file in @(Get-ChildItem -LiteralPath $jobsRoot -Filter '*.json' -File|Sort-Object Name)){
   $decoded=Read-ReconciledJobFile $file.FullName;$n=$decoded.normalized;$id=[string]$n.run_identifier
   if($known.ContainsKey($id)){throw 'duplicate normalized run identifier'};$known[$id]=$true
   $reconDirectory=Join-Path $reconRoot ($id+'.published');$reconPath=Join-Path $reconDirectory 'reconciliation.json';$reconciled=$false;$binding=$null
   if([string]$n.state -eq 'prepared'){
    if(Test-Path -LiteralPath $reconPath){$binding=Read-ReconciliationBinding $reconDirectory $id;$reconciled=$true}
   }elseif([string]$decoded.job.state -eq 'abandoned' -and $decoded.job.reconciliation_record_path){$binding=Read-ReconciliationBinding (Split-Path -Parent ([string]$decoded.job.reconciliation_record_path)) $id;$reconciled=$true}
   $validStates=$activeStates+@('prepared')+$terminalStates
   if([string]$n.state -notin $validStates){throw 'unknown job state'}
   $currentChanged=if($binding){$binding.original_sha256-ne(Hash-Bytes $decoded.raw)}else{$false}
   $rows+=[ordered]@{run_identifier=$id;normalized_state=[string]$n.state;reconciled_historical_prepared=$reconciled;original_binding_path=if($binding){$binding.original_path}else{$null};original_job_size=if($binding){$binding.original_size}else{$null};original_job_sha256=if($binding){$binding.original_sha256}else{$null};current_job_changed_after_reconciliation=$currentChanged}
  }
 }
 # Every published reconciliation must have exactly one source job and matching bytes.
 if(Test-Path -LiteralPath $reconRoot -PathType Container){
  foreach($dir in @(Get-ChildItem -LiteralPath $reconRoot -Directory -Filter '*.published'|Sort-Object Name)){
   $id=$dir.Name.Substring(0,$dir.Name.Length-10);$recordPath=Join-Path $dir.FullName 'reconciliation.json'
   if(!$known.ContainsKey($id)){throw 'reconciliation has no source job'}
   if(!(Test-Path -LiteralPath $recordPath -PathType Leaf)){throw 'published reconciliation incomplete'}
   $source=Join-Path $jobsRoot ($id+'.json');$decoded=Read-ReconciledJobFile $source;$null=Read-ReconciliationBinding $dir.FullName $id
  }
 }
 $active=@($rows|Where-Object{$_.normalized_state -in $activeStates}).Count
 $pending=@($rows|Where-Object{$_.normalized_state -in $pendingStates -and !$_.reconciled_historical_prepared}).Count
 $prepared=@($rows|Where-Object{$_.normalized_state -eq 'prepared' -and !$_.reconciled_historical_prepared}).Count
 [ordered]@{active_job_count=$active;pending_job_count=$pending;unresolved_prepared_job_count=$prepared;reconciled_historical_prepared_count=@($rows|Where-Object{$_.reconciled_historical_prepared}).Count;job_count=$rows.Count;jobs=$rows;verdict='PASS'}
}
function Get-NoraScheduledTaskInventory([string]$RunId){
 # Approved read-only ownership contract: repository NoraPhase2 task names/paths or exact run identity.
 @((Get-ScheduledTask -ErrorAction Stop)|Where-Object{
  $name=[string]$_.TaskName;$path=[string]$_.TaskPath
  $name -match '^NoraPhase2(?:Containment|Evidence|Qualification)(?:-|$)' -or
  $path -match '\\NoraPhase2(?:\\|$)' -or
  $name -like ('*'+$RunId+'*') -or $path -like ('*'+$RunId+'*')
 }|Sort-Object TaskPath,TaskName)
}
if($Mode -eq 'inventory'){
 if(!(Test-Path -LiteralPath $EvidenceRoot -PathType Container)){throw 'missing evidence root'}
 $jobs=Get-ReconciledJobInventory $EvidenceRoot
 if(!$QualificationId){throw 'qualification identity required for scheduled task inventory'}
 $tasks=@(Get-NoraScheduledTaskInventory $QualificationId)
 $jobs.scheduled_nora_task_count=$tasks.Count;$jobs.scheduled_nora_tasks=@($tasks|ForEach-Object{[ordered]@{task_path=[string]$_.TaskPath;task_name=[string]$_.TaskName}})
 $jobs|ConvertTo-Json -Depth 20 -Compress
}
