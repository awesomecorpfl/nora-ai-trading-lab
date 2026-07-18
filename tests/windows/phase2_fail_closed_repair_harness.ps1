[CmdletBinding()]
param(
 [Parameter(Mandatory=$true)][string]$QualificationScript,
 [Parameter(Mandatory=$true)][string]$RunnerScript,
 [Parameter(Mandatory=$true)][string]$OperatorStateHelper,
 [Parameter(Mandatory=$true)][string]$RestorationScript
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
function Assert-Parse([string]$Path){
 if(!(Test-Path -LiteralPath $Path -PathType Leaf)){throw ('missing validation script: '+$Path)}
 $tokens=$null;$errors=$null
 [Management.Automation.Language.Parser]::ParseFile($Path,[ref]$tokens,[ref]$errors)|Out-Null
 if(@($errors).Count-ne0){throw ('PowerShell parser failure '+$Path+': '+(@($errors|ForEach-Object{$_.Message})-join'; '))}
}
function Invoke-Child([string]$Script,[string[]]$Arguments){
 $old=$ErrorActionPreference;$ErrorActionPreference='Continue'
 $output=@(& powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $Script @Arguments 2>&1)
 $code=$LASTEXITCODE;$ErrorActionPreference=$old
 [ordered]@{exit_code=$code;output=($output -join "`n")}
}
foreach($path in @($QualificationScript,$RunnerScript,$OperatorStateHelper,$RestorationScript)){Assert-Parse $path}
if(@(Get-Process terminal64,metatester64 -ErrorAction SilentlyContinue).Count-ne0){throw 'terminal_or_tester_exists_before_synthetic_validation'}
$restorationTokens=$null;$restorationErrors=$null
$restorationAst=[Management.Automation.Language.Parser]::ParseFile($RestorationScript,[ref]$restorationTokens,[ref]$restorationErrors)
foreach($functionName in @('Canonical','SemanticRule','UnrelatedDigest')){
 $functionAst=$restorationAst.Find({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq $functionName},$true)
 if($null-eq$functionAst){throw ('restoration function missing: '+$functionName)}
 Invoke-Expression $functionAst.Extent.Text
}
$script:Guid='{AE6A1199-33B0-4109-B850-F1BB61AF0F6B}'
$unrelatedDigestOne=UnrelatedDigest;$unrelatedDigestTwo=UnrelatedDigest
if($unrelatedDigestOne-notmatch'^[0-9a-f]{64}$'-or$unrelatedDigestOne-ne$unrelatedDigestTwo){throw 'unrelated firewall semantic digest is not deterministic'}
$base=Join-Path $env:TEMP ('nora-pi0-repair-'+[guid]::NewGuid().ToString('N'))
try {
 $qualificationId='synthetic-repair-identity'
 $deployment=Join-Path $base 'deployment';$evidence=Join-Path $base 'evidence'
 New-Item -ItemType Directory -Path $deployment,$evidence -Force|Out-Null
 foreach($name in @('phase2-network-containment.ps1','phase2-fresh-verifier-arguments.ps1','phase2-network-containment-fresh-verify.ps1')){[IO.File]::WriteAllText((Join-Path $deployment $name),'# synthetic nonexecuted component',[Text.UTF8Encoding]::new($false))}
 [IO.File]::WriteAllText((Join-Path $evidence ('burned-'+$qualificationId+'-cleanup.json')),'{}',[Text.UTF8Encoding]::new($false))
 $reuse=Invoke-Child $QualificationScript @('-QualificationId',$qualificationId,'-DeployedRoot',$deployment,'-EvidenceBase',$evidence)
 if($reuse.exit_code-eq0-or$reuse.output-notmatch'NORA_QUALIFICATION_IDENTITY_REUSE_REJECTED'){throw 'burned qualification identity was not rejected before execution'}
 if(Test-Path -LiteralPath (Join-Path $evidence ('qualification-'+$qualificationId))){throw 'qualification root was created despite burned identity'}

 $runnerTokens=$null;$runnerErrors=$null
 $runnerAst=[Management.Automation.Language.Parser]::ParseFile($RunnerScript,[ref]$runnerTokens,[ref]$runnerErrors)
 if(@($runnerErrors).Count-ne0){throw 'runner parser failure before guard extraction'}
 foreach($functionName in @('ReadReconciliationJob','NoCampaignJob')){
  $functionAst=$runnerAst.Find({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq $functionName},$true)
  if($null-eq$functionAst){throw ('runner function missing: '+$functionName)}
  Invoke-Expression $functionAst.Extent.Text
 }
 $script:EvidenceRoot=Join-Path $base 'runner';$script:RunId='current-run'
 $jobs=Join-Path $script:EvidenceRoot 'jobs';New-Item -ItemType Directory -Path $jobs -Force|Out-Null
 function Paths(){[ordered]@{job=(Join-Path $script:EvidenceRoot ('jobs\'+$script:RunId+'.json'))}}
 function BoundProcess($Binding){return $false}
 @{schema_version='nora.phase2_persistent_evidence_runner_v1';run_identifier=$script:RunId;state='prepared'}|ConvertTo-Json -Compress|Set-Content -LiteralPath ((Paths).job) -Encoding utf8 -NoNewline
 NoCampaignJob
 $competing=Join-Path $jobs 'competing-run.json';@{schema_version='nora.phase2_persistent_evidence_runner_v1';run_identifier='competing-run';state='prepared'}|ConvertTo-Json -Compress|Set-Content -LiteralPath $competing -Encoding utf8 -NoNewline
 $competingRejected=$false;try{NoCampaignJob}catch{if($_.Exception.Message-eq'conflicting unresolved prepared campaign job'){$competingRejected=$true}else{throw}}
 if(!$competingRejected){throw 'competing prepared job was not rejected'}
 Remove-Item -LiteralPath $competing -Force
 $legacy=Join-Path $jobs 'legacy-competing-run.json';@{Keys=@('schema_version','run_identifier','state');Values=@('nora.phase2_persistent_evidence_runner_v1','legacy-competing-run','prepared')}|ConvertTo-Json -Compress|Set-Content -LiteralPath $legacy -Encoding utf8 -NoNewline
 $legacyRejected=$false;try{NoCampaignJob}catch{if($_.Exception.Message-eq'conflicting unresolved prepared campaign job'){$legacyRejected=$true}else{throw}}
 if(!$legacyRejected){throw 'legacy competing prepared job was not rejected'}

 $zeros40='0'*40;$zeros64='0'*64
 $selfHash=Invoke-Child $RestorationScript @('-Mode','preconditions','-EvidenceRoot',$evidence,'-RepositoryCommit',$zeros40,'-HelperSha256',$zeros64,'-RestorationScriptSha256',$zeros64,'-PacketId','synthetic-self-hash')
 if($selfHash.exit_code-eq0-or$selfHash.output-notmatch'deployed restoration script hash mismatch'){throw 'restoration self-hash mismatch was not rejected before preconditions'}

 [ordered]@{
  schema_version='nora.phase2_pi0_fail_closed_repair_harness_v1'
  verdict='PASS'
  parser_file_count=4
  burned_qualification_identity='FAIL_AS_EXPECTED'
  qualification_root_created=$false
  current_prepared_job='PASS'
  competing_prepared_job='FAIL_AS_EXPECTED'
  legacy_competing_prepared_job='FAIL_AS_EXPECTED'
  unrelated_firewall_digest='PASS'
  restoration_self_hash='FAIL_AS_EXPECTED'
  firewall_mutation_invoked=$false
  mt5_invoked=$false
 }|ConvertTo-Json -Compress
} finally {
 Remove-Item -LiteralPath $base -Recurse -Force -ErrorAction SilentlyContinue
}
