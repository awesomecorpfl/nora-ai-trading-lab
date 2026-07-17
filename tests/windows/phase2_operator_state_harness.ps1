[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$HelperPath)
$ErrorActionPreference='Stop'
function Put-Json([string]$Path,$Value){$Value|ConvertTo-Json -Depth 20 -Compress|Set-Content -LiteralPath $Path -Encoding utf8 -NoNewline}
function Invoke-Inventory([string]$Root){$out=& powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $HelperPath -Mode inventory -EvidenceRoot $Root -QualificationId 'synthetic-operator-state';$code=$LASTEXITCODE;[ordered]@{code=$code;output=($out -join '')}}
$base=Join-Path $env:TEMP ('nora-operator-state-'+[guid]::NewGuid().ToString('N'));New-Item -ItemType Directory -Path (Join-Path $base 'jobs') -Force|Out-Null;New-Item -ItemType Directory -Path (Join-Path $base 'reconciliations') -Force|Out-Null
try {
 $completed=Join-Path $base 'jobs\completed.json';Put-Json $completed @{schema_version='nora.phase2_persistent_evidence_runner_v1';run_identifier='completed-1';state='completed';preflight_kind='offline_cache'}
 $prepared=Join-Path $base 'jobs\prepared-1.json';Put-Json $prepared @{schema_version='nora.phase2_persistent_evidence_runner_v1';run_identifier='prepared-1';state='prepared';preflight_kind='offline_cache'}
 $raw=[IO.File]::ReadAllBytes($prepared);$sha=([Security.Cryptography.SHA256]::Create().ComputeHash($raw)|ForEach-Object{$_.ToString('x2')})-join'';$rdir=Join-Path $base 'reconciliations\prepared-1.published';New-Item -ItemType Directory -Path $rdir|Out-Null;Put-Json (Join-Path $rdir 'reconciliation.json') @{schema_version='nora.phase2_prelaunch_reconciliation_v1';run_identifier='prepared-1';classification='ABANDONED_PRE_LAUNCH_NO_CONTAINMENT';accepted=$false;original_job_sha256=$sha}
 $safe=Invoke-Inventory $base;if($safe.code -ne 0 -or $safe.output -notmatch '"unresolved_prepared_job_count":0'){throw 'safe reconciled state failed'}
 Remove-Item -LiteralPath $rdir -Recurse -Force;$unresolved=Invoke-Inventory $base;if($unresolved.code -ne 0 -or $unresolved.output -notmatch '"unresolved_prepared_job_count":1'){throw 'unresolved prepared state was not reported'}
 Put-Json $prepared @{schema_version='nora.phase2_persistent_evidence_runner_v1';run_identifier='prepared-1';state='prepared';Keys=@('state');Values=@('completed')};$contradict=Invoke-Inventory $base;if($contradict.code -eq 0){throw 'contradictory state passed'}
 [ordered]@{verdict='PASS';safe_reconciled='PASS';unresolved_prepared='FAIL_AS_EXPECTED';contradictory_reconciliation='FAIL_AS_EXPECTED'}|ConvertTo-Json -Compress
} finally {Remove-Item -LiteralPath $base -Recurse -Force -ErrorAction SilentlyContinue}
