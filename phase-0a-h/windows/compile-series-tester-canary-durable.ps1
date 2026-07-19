param(
    [Parameter(Mandatory=$true)][string]$IncomingRoot,
    [Parameter(Mandatory=$true)][string]$RunId,
    [int]$TimeoutSeconds=300
)
# Phase-2R durable series tester compile helper.
# Mirrors phase-0a-h/windows/compile-slope-tester-canary.ps1 capture fidelity so
# canary.sma_cross_native can meet the self_contained_raw_native standard set by
# Phase-2N slope. Does NOT modify the frozen compile-series-tester-canary.ps1.
$ErrorActionPreference='Stop'

$root="$env:USERPROFILE\NoraPhase2R"
$run=Join-Path $root $RunId
$source=Join-Path $run 'source'
$compileStart=(Get-Date).ToUniversalTime()
New-Item -ItemType Directory -Force $source | Out-Null

foreach($name in @('NoraPhase2RuntimeV1.mqh','NoraPhase2ConditionV1.mqh','NoraPhase2SeriesRuntimeV1.mqh','NoraPhase2SeriesTesterCanaryV1.mq5')){
    Copy-Item (Join-Path $IncomingRoot $name) (Join-Path $source $name) -Force
}

$runtimeSrc = Join-Path $source 'NoraPhase2RuntimeV1.mqh'
$conditionSrc = Join-Path $source 'NoraPhase2ConditionV1.mqh'
$seriesRuntimeSrc = Join-Path $source 'NoraPhase2SeriesRuntimeV1.mqh'
$testerSrc = Join-Path $source 'NoraPhase2SeriesTesterCanaryV1.mq5'
$runtimeSha = (Get-FileHash $runtimeSrc -Algorithm SHA256).Hash.ToLowerInvariant()
$conditionSha = (Get-FileHash $conditionSrc -Algorithm SHA256).Hash.ToLowerInvariant()
$seriesRuntimeSha = (Get-FileHash $seriesRuntimeSrc -Algorithm SHA256).Hash.ToLowerInvariant()
$testerSha = (Get-FileHash $testerSrc -Algorithm SHA256).Hash.ToLowerInvariant()

$editor='C:\Program Files\Darwinex MetaTrader 5\MetaEditor64.exe'
if(!(Test-Path $editor)){ throw 'configured MetaEditor64.exe absent' }

$program=$testerSrc
$log=Join-Path $run 'compile.log'
$sourceEx5=Join-Path $source 'NoraPhase2SeriesTesterCanaryV1.ex5'
$out=Join-Path $run 'NoraPhase2SeriesTesterCanaryV1.ex5'

$sourceEx5ExistedBefore=Test-Path $sourceEx5
$outputEx5ExistedBefore=Test-Path $out
if($sourceEx5ExistedBefore){ Remove-Item $sourceEx5 -Force }
if($outputEx5ExistedBefore){ Remove-Item $out -Force }
$sourceEx5ExistedImmediatelyBefore=Test-Path $sourceEx5
$outputEx5ExistedImmediatelyBefore=Test-Path $out

$argumentArray=@('/compile:"'+$program+'"','/log:"'+$log+'"')
$renderedCommand=$editor+' '+($argumentArray -join ' ')
$p=Start-Process -FilePath $editor -ArgumentList $argumentArray -PassThru

if(!$p.WaitForExit($TimeoutSeconds*1000)){ Stop-Process $p -Force; throw 'compiler timeout' }
$compileComplete=(Get-Date).ToUniversalTime()
if(!(Test-Path $log)){ throw 'compiler log absent' }

$text=Get-Content $log -Raw
$e=[regex]::Matches($text,'(?i)(\d+)\s+errors?')
$w=[regex]::Matches($text,'(?i)(\d+)\s+warnings?')
if($e.Count -eq 0 -or $w.Count -eq 0){ throw 'compiler log lacks deterministic error/warning counts' }

$errors=[int]$e[$e.Count-1].Groups[1].Value
$warnings=[int]$w[$w.Count-1].Groups[1].Value
$diagnosticLines=@($text -split "`r?`n" | Where-Object {$_ -match '(?i)\berrors?\b|\bwarnings?\b'})
$size=0
$sha=''
$ex5LastWrite=$null

if(Test-Path $sourceEx5){ Copy-Item $sourceEx5 $out -Force }
$ex5Exists=Test-Path $out
if($ex5Exists){
    $item=Get-Item $out
    $size=$item.Length
    $ex5LastWrite=$item.LastWriteTimeUtc.ToString('o')
    if($size -gt 0){ $sha=(Get-FileHash $out -Algorithm SHA256).Hash.ToLowerInvariant() }
}

$ex5AfterStart=$false
$ex5WithinCompletionAllowance=$false
if($ex5LastWrite){
    $ex5Time=[DateTime]::Parse($ex5LastWrite).ToUniversalTime()
    $ex5AfterStart=$ex5Time -ge $compileStart
    $ex5WithinCompletionAllowance=$ex5Time -le $compileComplete.AddSeconds(2)
}

$status=if($errors -eq 0 -and $warnings -eq 0 -and $size -gt 0 -and !$sourceEx5ExistedImmediatelyBefore -and !$outputEx5ExistedImmediatelyBefore -and $ex5AfterStart -and $ex5WithinCompletionAllowance){'compiled'}else{'failed'}

# Frozen source hashes — must match accepted fixture constants.
$RUNTIME_SOURCE_SHA256='97de0194d7715b32ce104a9889d1a4af46cff6d0759d637f21e41025a98ee043'
$CONDITION_SOURCE_SHA256='1c630ede14e103a62490573c746f7652cb3083096c9259711ee3c979229108a4'
$SERIES_RUNTIME_SOURCE_SHA256='6fbbe35045be59cdf571a623e38a213ca053be32fab153f858d461c1d4ac1b2d'
$SERIES_TESTER_SOURCE_SHA256='bc62801db8965d268e192d3dadb8ba7b11a7c5e3d5a432fbadd3f2241a4d2757'

if($runtimeSha -ne $RUNTIME_SOURCE_SHA256){ throw "runtime source hash mismatch: $runtimeSha" }
if($conditionSha -ne $CONDITION_SOURCE_SHA256){ throw "condition source hash mismatch: $conditionSha" }
if($seriesRuntimeSha -ne $SERIES_RUNTIME_SOURCE_SHA256){ throw "series runtime source hash mismatch: $seriesRuntimeSha" }
if($testerSha -ne $SERIES_TESTER_SOURCE_SHA256){ throw "series tester source hash mismatch: $testerSha" }

$result=[ordered]@{
    status=$status
    run_id=$RunId
    compiler_path=$editor
    argument_array=$argumentArray
    rendered_command=$renderedCommand
    working_directory=$source
    compile_start_utc=$compileStart.ToString('o')
    compile_completion_utc=$compileComplete.ToString('o')
    native_process_exit_status=$p.ExitCode
    compiler_exit_code=$p.ExitCode
    compiler_version=(Get-Item $editor).VersionInfo.FileVersion
    source_paths=[ordered]@{
        runtime=$runtimeSrc
        condition=$conditionSrc
        series_runtime=$seriesRuntimeSrc
        tester=$program
    }
    compile_log_path=$log
    ex5_path=$out
    source_ex5_existed_before=$sourceEx5ExistedBefore
    output_ex5_existed_before=$outputEx5ExistedBefore
    source_ex5_existed_immediately_before=$sourceEx5ExistedImmediatelyBefore
    output_ex5_existed_immediately_before=$outputEx5ExistedImmediatelyBefore
    error_count=$errors
    warning_count=$warnings
    diagnostic_lines=$diagnosticLines
    ex5_exists=$ex5Exists
    ex5_last_write_time_utc=$ex5LastWrite
    ex5_size_bytes=$size
    ex5_sha256=$sha
    filesystem_resolution_allowance_seconds=2
    ex5_after_compile_start=$ex5AfterStart
    ex5_within_completion_allowance=$ex5WithinCompletionAllowance
    ex5_filename='NoraPhase2SeriesTesterCanaryV1.ex5'
    runtime_source_sha256=$runtimeSha
    condition_source_sha256=$conditionSha
    series_runtime_source_sha256=$seriesRuntimeSha
    series_tester_source_sha256=$testerSha
}

$nativeEvidence=[ordered]@{
    rendered_command=$renderedCommand
    compile_log_path=$log
    compile_start_utc=$compileStart.ToString('o')
    compile_completion_utc=$compileComplete.ToString('o')
    compiler_path=$editor
    compiler_version=(Get-Item $editor).VersionInfo.FileVersion
    compiler_exit_code=$p.ExitCode
    native_process_exit_status=$p.ExitCode
    error_count=$errors
    warning_count=$warnings
    ex5_exists=$ex5Exists
    ex5_filename='NoraPhase2SeriesTesterCanaryV1.ex5'
    ex5_path=$out
    ex5_sha256=$sha
    ex5_size_bytes=$size
    ex5_last_write_time_utc=$ex5LastWrite
    ex5_after_compile_start=$ex5AfterStart
    ex5_within_completion_allowance=$ex5WithinCompletionAllowance
    source_ex5_existed_before=$sourceEx5ExistedBefore
    output_ex5_existed_before=$outputEx5ExistedBefore
    source_ex5_existed_immediately_before=$sourceEx5ExistedImmediatelyBefore
    output_ex5_existed_immediately_before=$outputEx5ExistedImmediatelyBefore
    filesystem_resolution_allowance_seconds=2
    diagnostic_lines=$diagnosticLines
}
$result['native_evidence']=$nativeEvidence

$result | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $run 'compile.json') -Encoding utf8
if($status -ne 'compiled'){ exit 2 }
