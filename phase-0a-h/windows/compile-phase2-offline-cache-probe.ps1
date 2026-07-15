param(
 [Parameter(Mandatory=$true)][string]$Source,
 [Parameter(Mandatory=$true)][string]$Destination
)
$ErrorActionPreference='Stop'
$editor='C:\Program Files\Darwinex MetaTrader 5\MetaEditor64.exe'
if(!(Test-Path -LiteralPath $Source -PathType Leaf) -or !(Test-Path -LiteralPath $editor -PathType Leaf)){throw 'missing probe compiler input'}
function Hash([string]$Path){(Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()}
New-Item -ItemType Directory -Path $Destination -Force|Out-Null
$target=Join-Path $Destination 'NoraPhase2OfflineCacheProbeV1.mq5';Copy-Item -LiteralPath $Source -Destination $target -Force
$ex5=[IO.Path]::ChangeExtension($target,'.ex5');$log=Join-Path $Destination 'compile.log';if(Test-Path -LiteralPath $ex5){Remove-Item -LiteralPath $ex5 -Force};$start=(Get-Date).ToUniversalTime();$process=Start-Process -FilePath $editor -ArgumentList @('/compile:"'+$target+'"','/log:"'+$log+'"') -PassThru;if(!$process.WaitForExit(120000)){throw 'probe compiler timeout'};$end=(Get-Date).ToUniversalTime()
if(!(Test-Path -LiteralPath $log) -or !(Test-Path -LiteralPath $ex5)){throw 'probe compiler output absent'};$text=Get-Content -LiteralPath $log -Raw;if($text -notmatch 'Result:\s*0 errors,\s*0 warnings'){throw 'probe compiler diagnostics'}
$record=[ordered]@{schema_version='nora.phase2_mt5_cache_probe_compiler_v1';source_sha256=Hash $target;compiler_path=$editor;compiler_sha256=Hash $editor;compiler_version=(Get-Item $editor).VersionInfo.FileVersion;source_path='NoraPhase2OfflineCacheProbeV1.mq5';ex5_path='NoraPhase2OfflineCacheProbeV1.ex5';ex5_sha256=Hash $ex5;log_sha256=Hash $log;invocation_start_utc=$start.ToString('o');invocation_end_utc=$end.ToString('o');process_exit=$process.ExitCode};$record|ConvertTo-Json -Depth 8 -Compress|Set-Content -LiteralPath (Join-Path $Destination 'compiler-record.json') -Encoding utf8 -NoNewline;$record|ConvertTo-Json -Depth 8 -Compress
