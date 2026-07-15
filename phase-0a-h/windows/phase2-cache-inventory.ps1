param(
 [Parameter(Mandatory=$true)][string]$CacheRoot,
 [Parameter(Mandatory=$true)][string]$Destination
)
$ErrorActionPreference='Stop'
if(!(Test-Path -LiteralPath $CacheRoot -PathType Container)){throw 'missing cache root'}
function Hash([string]$Path){(Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()}
function AtomicJson([string]$Path,$Value){$tmp=$Path+'.partial.'+[guid]::NewGuid().ToString('N');$Value|ConvertTo-Json -Depth 12 -Compress|Set-Content -LiteralPath $tmp -Encoding utf8 -NoNewline;Move-Item -LiteralPath $tmp -Destination $Path}
$roots=@('history\GDAXI','history\AUDCAD','ticks\GDAXI','ticks\AUDCAD')|ForEach-Object{Join-Path $CacheRoot $_}
$files=@();foreach($root in $roots){if(Test-Path -LiteralPath $root){Get-ChildItem -LiteralPath $root -File -Recurse -Force|Sort-Object FullName|ForEach-Object{$rel=$_.FullName.Substring($CacheRoot.Length).TrimStart('\').Replace('\','/');$year=if($_.Name -match '^(19|20)\d{2}\.hcc$'){[int]$_.BaseName}else{$null};$files+=[ordered]@{path=$rel;size=[int64]$_.Length;last_write_utc=$_.LastWriteTimeUtc.ToString('o');sha256=Hash $_.FullName;history_year=$year}}}}
$coverage=@{};foreach($symbol in @('GDAXI','AUDCAD')){$years=@($files|Where-Object{$_.path -like ('history/'+$symbol+'/*') -and $_.history_year -ne $null}|ForEach-Object{$_.history_year}|Sort-Object -Unique);$coverage[$symbol]=[ordered]@{years=$years;first_year=if($years.Count){$years[0]}else{$null};last_year=if($years.Count){$years[$years.Count-1]}else{$null}}}
$record=[ordered]@{schema_version='nora.phase2_mt5_cache_inventory_v1';cache_root_token='<MT5_CACHE_ROOT>';captured_utc=(Get-Date).ToUniversalTime().ToString('o');files=$files;coverage=$coverage};AtomicJson $Destination $record;$record|ConvertTo-Json -Depth 12 -Compress
