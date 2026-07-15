[CmdletBinding()]
param(
 [Parameter(Mandatory=$true)][string]$ContainmentPath,
 [Parameter(Mandatory=$true)][string]$FreshVerifierPath,
 [Parameter(Mandatory=$true)][string]$EvidenceRoot,
 [Parameter(Mandatory=$true)][string[]]$ExecutablePath
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
function Run([string]$Id,[string[]]$Paths,[bool]$ExpectedSuccess){
 $output=@(& $ContainmentPath -Action smoke -CampaignId $Id -EvidenceRoot $EvidenceRoot -ExecutablePath $Paths 2>&1)
 $success=$?
 [int]$exitCode=if(Test-Path -LiteralPath 'Variable:global:LASTEXITCODE'){[int]$global:LASTEXITCODE}elseif($success){0}else{1}
 if(($exitCode -eq 0) -ne $ExpectedSuccess){throw ('unexpected smoke verdict for '+$Id+': '+($output -join "`n"))}
 $json=$null;if($exitCode-eq0){$json=($output -join "`n")|ConvertFrom-Json;if($json.mutation_cmdlets_invoked -or @($json.synthetic_firewall_result_counts).Count-ne1 -or $json.synthetic_firewall_result_counts.zero-ne0 -or $json.synthetic_firewall_result_counts.one-ne1 -or $json.synthetic_firewall_result_counts.multiple-ne2){throw ('invalid collection-shape smoke output for '+$Id)}}
 return [ordered]@{id=$Id;expected_success=$ExpectedSuccess;actual_success=($exitCode-eq0);exit_code=$exitCode;output=($output -join "`n");result=$json}
}
if(!(Test-Path -LiteralPath $ContainmentPath -PathType Leaf)){throw 'missing containment smoke tool'}
if(!(Test-Path -LiteralPath $FreshVerifierPath -PathType Leaf)){throw 'missing fresh verifier smoke tool'}
if(@($ExecutablePath).Count -lt 1){throw 'missing smoke executable paths'}
$directory=(Get-Item -LiteralPath $ExecutablePath[0] -Force).Directory
$results=@()
$results += Run 'p2smokeone20260715a' @($ExecutablePath[0]) $true
if(@($ExecutablePath).Count -ge 2){$results += Run 'p2smoketwo20260715a' @($ExecutablePath[0],$ExecutablePath[1]) $true}
$results += Run 'p2smokemissing20260715a' @((Join-Path $directory.FullName 'missing-smoke.exe')) $false
$results += Run 'p2smokedirectory20260715a' @($directory.FullName) $false
$results += Run 'p2smoketraversal20260715a' @($ExecutablePath[0].Replace($directory.FullName,($directory.FullName+'\..\'+$directory.Name))) $false
function FreshRun([string]$Id,[string]$Path,[string]$ExpectedHash,[bool]$ExpectedSuccess){$oldErrorAction=$ErrorActionPreference;$ErrorActionPreference='Continue';$out=@(& powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $FreshVerifierPath -FinalRecordPath $Path -ExpectedFinalRecordSha256 $ExpectedHash -EvidenceRoot $EvidenceRoot 2>&1);$code=[int]$global:LASTEXITCODE;$ErrorActionPreference=$oldErrorAction;if(($code-eq0)-ne$ExpectedSuccess){throw ('unexpected fresh verifier verdict for '+$Id+': '+($out-join "`n"))};return [ordered]@{id=$Id;expected_success=$ExpectedSuccess;actual_success=($code-eq0);exit_code=$code;arguments=@('-FinalRecordPath',$Path,'-ExpectedFinalRecordSha256',$ExpectedHash,'-EvidenceRoot',$EvidenceRoot);output=($out-join "`n")}}
$fresh=@();$fresh+=FreshRun 'p2smokefreshwronghash20260715a' (Join-Path $EvidenceRoot 'containment-p2canok20260715e.json') ('0'*64) $false;$fresh+=FreshRun 'p2smokefreshoutsideroot20260715a' 'C:\NoraEvidence\Phase2-escape\synthetic.json' ('0'*64) $false
[ordered]@{schema_version='nora.phase2_containment_runtime_smoke_harness_v2';mutation_cmdlets_invoked=$false;repeated_executable_parameter_used=$false;results=$results;fresh_verification=$fresh;passed=(@($results|Where-Object{!$_.actual_success -ne !$_.expected_success}).Count-eq0 -and @($fresh|Where-Object{!$_.actual_success -ne !$_.expected_success}).Count-eq0)}|ConvertTo-Json -Depth 20 -Compress
