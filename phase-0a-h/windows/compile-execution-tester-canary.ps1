param([string]$IncomingRoot,[string]$RunId)
# Contract-only native handoff script. It is intentionally target-specific and is not run locally.
$target='execution';$runtime='NoraPhase2ExecutionRuntimeV1.mqh';$tester='NoraPhase2ExecutionTesterCanaryV1.mq5';$policy='nora.metaeditor_cli_success_v1'
if(!(Test-Path (Join-Path $IncomingRoot $runtime)) -or !(Test-Path (Join-Path $IncomingRoot $tester))){throw 'missing execution canary source'}
# A native runner must remove any prior EX5, bind both source hashes, require a fresh EX5 and zero-error/zero-warning compiler record.
@{target_identifier=$target;compiler_policy_version=$policy;runtime=$runtime;tester=$tester;require_fresh_ex5=$true;require_zero_errors=$true;require_zero_warnings=$true}|ConvertTo-Json -Compress
