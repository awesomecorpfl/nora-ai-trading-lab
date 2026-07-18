param(
 [Parameter(Mandatory=$true)][string]$IncomingRoot,
 [Parameter(Mandatory=$true)][string]$RunId
)
$ErrorActionPreference='Stop'
$target='phase2_ten_strategy_suite'
$policy='nora.metaeditor_cli_success_v1'
$editor='C:\Program Files\Darwinex MetaTrader 5\MetaEditor64.exe'
$build='5.0.0.5836'
$expectedTargetDescriptorIdentity='48dc3d7bf1de62f6fd5245888751a0fee38aaa16f17929c288ee1ff503772aea'
$expectedCompileInputIdentity='ecbffe6bb25e16a1fcf5b823132adf02542388ccfb61023e5f8249dde5490a2f'
$expectedRuntimeIdentity='bd6ad8af0eb5bfd844e815d07336fa91e1d1da391e389f3359d812695752febd'
$expectedTesterIdentity='91838ccb6d701de4f8fbef099505153c97f1dc0ee96a7229be51f656ff03a6ca'
$expectedRuntimeSha256='7ab94a2ccf07b68ed62d652cb1fa6522455fc96ac7facdd8ffbc0058f9a43a5c'
$expectedTesterSha256='b6424f27757d1213ad9d935bf6fcec9a71a09ebe68f698f2e9f7402d4eb14d9f'
$expectedCompilerOutputSchema='nora.ten_strategy_compiler_output_v1'
$expectedCompileEvidenceSchema='nora.ten_strategy_compile_evidence_manifest_v1'
$expectedRedactionPolicyIdentity='d3a8f91e856a458aa5ce6f24f6257842684dc460f071603dac85fa59a5e5fc78'
$ex5='NoraPhase2TenStrategyTesterCanaryV1.ex5'
$root=Join-Path $env:USERPROFILE 'NoraPhase2TenStrategyValidation\compile-v2'
$run=Join-Path $root $RunId
$evidence=Join-Path $run 'evidence'
function Hash([string]$Path){(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()}
function ReadJson([string]$Path){Get-Content -LiteralPath $Path -Raw|ConvertFrom-Json}
if(Test-Path -LiteralPath $run){throw 'occupied compile destination'}
New-Item -ItemType Directory -Path $evidence -Force|Out-Null
try {
 $inputPath=Join-Path $IncomingRoot 'compile_input.json'
 if(!(Test-Path -LiteralPath $inputPath)){throw 'missing compile input'}
 $input=ReadJson $inputPath
 if($input.target_identifier-ne$target -or $input.compiler_policy-ne$policy -or $input.target_descriptor_identity-ne$expectedTargetDescriptorIdentity -or $input.compile_input_identity-ne$expectedCompileInputIdentity -or $input.runtime_identity-ne$expectedRuntimeIdentity -or $input.tester_identity-ne$expectedTesterIdentity -or $input.runtime_sha256-ne$expectedRuntimeSha256 -or $input.tester_sha256-ne$expectedTesterSha256 -or $input.compiler_output_schema-ne$expectedCompilerOutputSchema -or $input.compile_evidence_schema-ne$expectedCompileEvidenceSchema -or $input.redaction_policy_identity-ne$expectedRedactionPolicyIdentity){throw 'contract identity binding mismatch'}
 if((Get-Item -LiteralPath $editor).VersionInfo.FileVersion-ne$build){throw 'unexpected MetaEditor build'}
 $runtimePath=Join-Path $IncomingRoot $input.runtime_source_path
 $testerPath=Join-Path $IncomingRoot $input.tester_source_path
 if(!(Test-Path -LiteralPath $runtimePath) -or !(Test-Path -LiteralPath $testerPath)){throw 'missing bound source'}
 if((Hash $runtimePath)-ne$input.runtime_sha256 -or (Hash $testerPath)-ne$input.tester_sha256){throw 'source hash mismatch'}
 $work=Join-Path $run 'compile';New-Item -ItemType Directory -Path $work -Force|Out-Null
 Copy-Item -LiteralPath $runtimePath -Destination $work -Force
 Copy-Item -LiteralPath $testerPath -Destination $work -Force
 $out=Join-Path $work $ex5;if(Test-Path -LiteralPath $out){Remove-Item -LiteralPath $out -Force}
 $rawLog=Join-Path $work 'compile.raw.log'
 $start=(Get-Date).ToUniversalTime()
 $procArgs=@('/compile:"'+(Join-Path $work (Split-Path $testerPath -Leaf))+'"','/log:"'+$rawLog+'"')
 $p=Start-Process -FilePath $editor -ArgumentList $procArgs -PassThru
 if(!$p.WaitForExit(120000)){$p.Kill();throw 'compiler timeout'}
 $end=(Get-Date).ToUniversalTime()
 if(!(Test-Path -LiteralPath $rawLog)){throw 'compiler log absent'}
 $rawBytes=[IO.File]::ReadAllBytes($rawLog)
 $rawText=[Text.Encoding]::Unicode.GetString($rawBytes)
 if($rawText.Length-gt0 -and [int]$rawText[0]-eq 0xFEFF){$rawText=$rawText.Substring(1)}
 $pathPattern='(?i)(?<![A-Za-z0-9_<>])([A-Z]):\\Users\\([^\\\r\n]+)'
 $pathMatches=[regex]::Matches($rawText,$pathPattern).Count
 if($pathMatches-eq0){throw 'compiler log has no redaction target'}
 $redactedText=[regex]::Replace($rawText,$pathPattern,'<WINDOWS_USER_PATH>')
 $redactedLog=Join-Path $evidence 'compile.redacted.log'
 [IO.File]::WriteAllText($redactedLog,$redactedText,[Text.Encoding]::Unicode)
 $line=@(Get-Content -LiteralPath $rawLog|Where-Object{$_-match '^Result:'})|Select-Object -Last 1
 if(!$line -or $line-notmatch 'Result:\s*(\d+) errors,\s*(\d+) warnings' -or [int]$matches[1]-ne0 -or [int]$matches[2]-ne0){throw 'compiler diagnostics'}
 if(!(Test-Path -LiteralPath $out) -or (Get-Item -LiteralPath $out).LastWriteTimeUtc-lt$start){throw 'stale or missing ex5'}
 $decision=if($p.ExitCode-eq0){'accepted_zero'}elseif($p.ExitCode-eq1){'accepted_metaeditor_5836_one'}else{throw 'unexpected compiler exit'}
 Copy-Item -LiteralPath $out -Destination (Join-Path $evidence $ex5) -Force
 $record=[ordered]@{
  schema_version=$input.compiler_output_schema;target_identifier=$target;target_descriptor_identity=$input.target_descriptor_identity;compile_input_identity=$input.compile_input_identity
  runtime_sha256=Hash $runtimePath;tester_sha256=Hash $testerPath;package_identity=$input.package_identity
  metaeditor_executable=$editor;observed_metaeditor_build=$build;exact_command=($editor+' '+($procArgs-join' '));invocation_start_utc=$start.ToString('o');invocation_completion_utc=$end.ToString('o')
  raw_process_exit=$p.ExitCode;normalized_result='success';compiler_policy=$policy;policy_decision=$decision
  log_path='compile.redacted.log';log_size=(Get-Item -LiteralPath $redactedLog).Length;log_sha256=Hash $redactedLog
  raw_log_size=$rawBytes.Length;raw_log_sha256=([BitConverter]::ToString(([Security.Cryptography.SHA256]::Create()).ComputeHash($rawBytes))).Replace('-','').ToLowerInvariant()
  redacted_log_size=(Get-Item -LiteralPath $redactedLog).Length;redacted_log_sha256=Hash $redactedLog;redacted_path_occurrences=$pathMatches
  redaction_policy_version='nora.compiler_log_path_redaction_v1';redaction_policy_identity=$input.redaction_policy_identity;redaction_placeholder='<WINDOWS_USER_PATH>';raw_log_preservation='external_isolated_windows_evidence'
  warning_count=0;warnings=@();error_count=0;errors=@();ex5_path=$ex5;ex5_size=(Get-Item (Join-Path $evidence $ex5)).Length;ex5_sha256=Hash (Join-Path $evidence $ex5)
  freshness_proof=@{preexisting_ex5_removed_or_isolated=$true;produced_after_invocation_start=$true;single_unambiguous_ex5=$true};completion_state='completed';failure_reason=$null
 }
 $record|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $evidence 'compiler_record.json') -Encoding utf8
 $manifest=[ordered]@{schema_version=$input.compile_evidence_schema;target_identifier=$target;target_descriptor_identity=$input.target_descriptor_identity;compile_input_identity=$input.compile_input_identity}
 $manifest|ConvertTo-Json -Compress|Set-Content -LiteralPath (Join-Path $evidence 'compile_evidence_manifest.json') -Encoding utf8
 $inventory=@();foreach($pair in @(@('compiler_record.json','compiler_record'),@('compile.redacted.log','compiler_log'),@($ex5,'compiled_ex5'),@('compile_evidence_manifest.json','compile_evidence_manifest'))){$f=Join-Path $evidence $pair[0];$inventory+=@{path=$pair[0];role=$pair[1];sha256=Hash $f;size=(Get-Item -LiteralPath $f).Length}}
 $inventory|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $evidence 'inventory.json') -Encoding utf8
 Write-Output $evidence
} catch {Remove-Item -LiteralPath $run -Recurse -Force -ErrorAction SilentlyContinue;throw}
