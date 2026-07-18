[CmdletBinding()]
param(
 [Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9][A-Za-z0-9._-]{7,127}$')][string]$QualificationId,
 [string]$DeployedRoot='C:\NoraEvidence\Phase2\frt1r2-inert-b56c188',
 [string]$EvidenceBase='C:\NoraEvidence\Phase2'
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$containment=Join-Path $DeployedRoot 'phase2-network-containment.ps1'
$helper=Join-Path $DeployedRoot 'phase2-fresh-verifier-arguments.ps1'
$verifier=Join-Path $DeployedRoot 'phase2-network-containment-fresh-verify.ps1'
function Hash([string]$Path){(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()}
function AtomicJson([string]$Path,$Value){if(Test-Path -LiteralPath $Path){throw 'immutable qualification artifact exists'};$tmp=$Path+'.partial.'+[guid]::NewGuid().ToString('N');$Value|ConvertTo-Json -Depth 20 -Compress|Set-Content -LiteralPath $tmp -Encoding utf8 -NoNewline;[IO.File]::Move($tmp,$Path)}
foreach($path in @($containment,$helper,$verifier)){if(!(Test-Path -LiteralPath $path -PathType Leaf)){throw 'missing deployed qualification component'}}
if(@(Get-Process terminal64,metatester64 -ErrorAction SilentlyContinue).Count){throw 'terminal_or_tester_exists_before_qualification'}
if(!(Test-Path -LiteralPath $EvidenceBase -PathType Container)){throw 'missing qualification evidence base'}
$identityCollisions=@(Get-ChildItem -LiteralPath $EvidenceBase -Force -ErrorAction Stop|Where-Object{$_.Name -like ('*'+$QualificationId+'*')})
if($identityCollisions.Count-ne0){throw 'NORA_QUALIFICATION_IDENTITY_REUSE_REJECTED'}
$evidence=Join-Path $EvidenceBase ('qualification-'+$QualificationId);New-Item -ItemType Directory -Path $evidence -ErrorAction Stop|Out-Null
$final=Join-Path $evidence ('containment-'+$QualificationId+'.json');$accepted=Join-Path $evidence ('containment-'+$QualificationId+'.transaction-accepted.json');$cleanup=Join-Path $evidence ('containment-'+$QualificationId+'-cleanup.json');$tokenRecord=Join-Path $evidence 'argument-tokens.json';$result=Join-Path $evidence 'qualification-result.json';$staged=$false
try {
 & $containment -Action stage -CampaignId $QualificationId -EvidenceRoot $evidence|Out-Null;$staged=$true
 if(!(Test-Path -LiteralPath $accepted -PathType Leaf)){throw 'containment acceptance absent'}
 . $helper
 $tokens=@(New-NoraFreshVerifierArgumentVector -VerifierPath $verifier -FinalRecordPath $final -ExpectedFinalRecordSha256 (Hash $final) -EvidenceRoot $evidence)
 AtomicJson $tokenRecord ([ordered]@{schema_version='nora.phase2_frt1r2_argument_tokens_v1';qualification_id=$QualificationId;tokens=@($tokens);final_record_path=$final;final_record_sha256=Hash $final;literal_path_token_count=@($tokens|Where-Object{$_ -eq '-LiteralPath'}).Count;authoritative_path_parameter_count=@($tokens|Where-Object{$_ -eq '-FinalRecordPath'}).Count})
 if(@(Get-Process terminal64,metatester64 -ErrorAction SilentlyContinue).Count){throw 'terminal_or_tester_exists_after_qualification'}
} finally {
 $cleanupFailure=$null
 try { & $containment -Action cleanup -CampaignId $QualificationId -EvidenceRoot $evidence|Out-Null;if($LASTEXITCODE-ne0){throw ('cleanup exited '+[string]$LASTEXITCODE)} } catch { $cleanupFailure=$_ }
 if($cleanupFailure){throw $cleanupFailure}
}
if(!(Test-Path -LiteralPath $cleanup -PathType Leaf)){throw 'cleanup evidence absent'}
AtomicJson $result ([ordered]@{schema_version='nora.phase2_frt1r2_containment_only_qualification_v1';qualification_id=$QualificationId;native_execution_started=$false;history_accessed=$false;market_data_accessed=$false;accepted_path=$accepted;accepted_sha256=Hash $accepted;argument_tokens_path=$tokenRecord;argument_tokens_sha256=Hash $tokenRecord;cleanup_path=$cleanup;cleanup_sha256=Hash $cleanup;repeated_cleanup_required=$true;completed_utc=(Get-Date).ToUniversalTime().ToString('o')})
Get-Content -LiteralPath $result -Raw