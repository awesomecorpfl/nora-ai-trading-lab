param(
 [Parameter(Mandatory=$true)][ValidateSet('before','after')][string]$Phase,
 [Parameter(Mandatory=$true)][string]$CacheRoot,
 [Parameter(Mandatory=$true)][string]$Destination,
 [Parameter(Mandatory=$true)][long]$ObservedBarCount,
 [Parameter(Mandatory=$true)][string]$EarliestHistoryTimestamp,
 [Parameter(Mandatory=$true)][string]$LatestHistoryTimestamp
)
$ErrorActionPreference='Stop'
function Hash([string]$Path){(Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()}
if(!(Test-Path -LiteralPath $CacheRoot -PathType Container)){throw 'missing cache root'}
$files=@()
Get-ChildItem -LiteralPath $CacheRoot -Recurse -File | Sort-Object FullName | ForEach-Object {
 $relative=$_.FullName.Substring($CacheRoot.Length).TrimStart('\').Replace('\','/')
 $files += [ordered]@{path=$relative;size=$_.Length;last_write_utc=$_.LastWriteTimeUtc.ToString('o');sha256=Hash $_.FullName}
}
$record=[ordered]@{schema_version='nora.ten_strategy_environment_inventory_v2';phase=$Phase;cache_root_token='<MT5_CACHE_ROOT>';observed_bar_count=$ObservedBarCount;earliest_history_timestamp=$EarliestHistoryTimestamp;latest_history_timestamp=$LatestHistoryTimestamp;files=$files}
$record|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $Destination -Encoding utf8
