param(
  [Parameter(Mandatory=$true)][string]$IncomingRoot,
  [Parameter(Mandatory=$true)][string]$RunId,
  [int]$TimeoutSeconds=300
)
$ErrorActionPreference='Stop'
$root="$env:USERPROFILE\NoraPhase2I";$run=Join-Path $root $RunId;$source=Join-Path $run 'source';New-Item -ItemType Directory -Force $source|Out-Null
foreach($name in @('NoraPhase2RuntimeV1.mqh','NoraPhase2ConditionV1.mqh','NoraPhase2ConditionFixtureV1.mq5')){Copy-Item (Join-Path $IncomingRoot $name) (Join-Path $source $name) -Force}
$editor='C:\Program Files\Darwinex MetaTrader 5\MetaEditor64.exe';if(!(Test-Path $editor)){throw 'configured MetaEditor64.exe absent'}
$compilerVersion=(Get-Item $editor).VersionInfo.FileVersion;$script=Join-Path $source 'NoraPhase2ConditionFixtureV1.mq5';$log=Join-Path $run 'compile.log';$ex5=Join-Path $source 'NoraPhase2ConditionFixtureV1.ex5'
$process=Start-Process $editor -ArgumentList ('/compile:"'+$script+'" /log:"'+$log+'"') -PassThru
if(!$process.WaitForExit($TimeoutSeconds*1000)){Stop-Process $process -Force;throw 'compiler timeout'}
$exitCode=$process.ExitCode;if(!(Test-Path $log)){throw 'compiler log absent'}
$text=Get-Content $log -Raw;$errorMatches=[regex]::Matches($text,'(?i)(\d+)\s+errors?');$warningMatches=[regex]::Matches($text,'(?i)(\d+)\s+warnings?')
if($errorMatches.Count -eq 0 -or $warningMatches.Count -eq 0){throw 'compiler log lacks deterministic error/warning counts'}
$errors=[int]$errorMatches[$errorMatches.Count-1].Groups[1].Value;$warnings=[int]$warningMatches[$warningMatches.Count-1].Groups[1].Value;$size=0;$sha='';$retrievedEx5=Join-Path $run 'NoraPhase2ConditionFixtureV1.ex5'
if(Test-Path $ex5){Copy-Item $ex5 $retrievedEx5 -Force;$size=(Get-Item $retrievedEx5).Length;if($size -gt 0){$sha=(Get-FileHash $retrievedEx5 -Algorithm SHA256).Hash.ToLowerInvariant()}}
$status=if($errors -eq 0 -and $warnings -eq 0 -and $size -gt 0){'compiled'}else{'failed'}
$result=[ordered]@{status=$status;compiler_path=$editor;compiler_version=$compilerVersion;compiler_exit_code=$exitCode;error_count=$errors;warning_count=$warnings;ex5_filename='NoraPhase2ConditionFixtureV1.ex5';ex5_size_bytes=$size;ex5_sha256=$sha}
$result|ConvertTo-Json -Compress|Set-Content (Join-Path $run 'compile.json') -Encoding utf8
$result|ConvertTo-Json -Compress
if($status -ne 'compiled'){exit 2}
