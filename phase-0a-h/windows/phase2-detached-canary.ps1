param(
 [Parameter(Mandatory=$true)][string]$RunId,
 [Parameter(Mandatory=$true)][string]$RunDirectory,
 [Parameter(Mandatory=$true)][ValidateSet('success','intentional-failure','disconnect','forced-termination')][string]$CanaryKind
)
$ErrorActionPreference='Stop'
if($RunId-notmatch'^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$'){throw 'invalid canary run identity'}
if(!(Test-Path -LiteralPath $RunDirectory -PathType Container)){throw 'missing canary run directory'}
function AtomicJson([string]$Path,$Value){$tmp=$Path+'.partial.'+[guid]::NewGuid().ToString('N');$Value|ConvertTo-Json -Depth 8 -Compress|Set-Content -LiteralPath $tmp -Encoding utf8 -NoNewline;if(Test-Path -LiteralPath $Path){$backup=$Path+'.replace-backup.'+[guid]::NewGuid().ToString('N');[IO.File]::Replace($tmp,$Path,$backup);Remove-Item -LiteralPath $backup -Force}else{[IO.File]::Move($tmp,$Path)}}
function Progress([string]$Step){AtomicJson (Join-Path $RunDirectory 'canary-progress.json') ([ordered]@{schema_version='nora.phase2_detached_canary_progress_v1';run_identifier=$RunId;canary_kind=$CanaryKind;step=$Step;pid=$PID;utc=(Get-Date).ToUniversalTime().ToString('o')})}
Progress 'workload-entered'
switch($CanaryKind){
 'success' {Start-Sleep -Seconds 2;Progress 'sleep-completed'}
 'disconnect' {Start-Sleep -Seconds 20;Progress 'continued-after-launch-connection'}
 'forced-termination' {Start-Sleep -Seconds 30;Progress 'unexpected-unforced-completion'}
 'intentional-failure' {Start-Sleep -Milliseconds 250;Progress 'intentional-failure-armed';throw 'NORA_INTENTIONAL_DETACHED_CANARY_FAILURE'}
}
