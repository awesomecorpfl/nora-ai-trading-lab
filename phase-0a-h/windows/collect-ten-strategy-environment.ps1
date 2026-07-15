param(
 [Parameter(Mandatory=$true)][ValidateSet('before','after')][string]$Phase,
 [Parameter(Mandatory=$true)][string]$TerminalDataDirectory,
 [Parameter(Mandatory=$true)][string]$TerminalPath,
 [Parameter(Mandatory=$true)][string]$ConfigurationPath,
 [Parameter(Mandatory=$true)][ValidateSet('GDAXI','AUDCAD')][string]$Symbol,
 [Parameter(Mandatory=$true)][string]$ResolverPath,
 [Parameter(Mandatory=$true)][string]$Destination,
 [Parameter(Mandatory=$true)][long]$ObservedBarCount,
 [Parameter(Mandatory=$true)][string]$EarliestHistoryTimestamp,
 [Parameter(Mandatory=$true)][string]$LatestHistoryTimestamp
)
$ErrorActionPreference='Stop'
if(!(Test-Path -LiteralPath $ResolverPath -PathType Leaf)){throw 'missing server scope resolver'}
$scope=((& $ResolverPath -TerminalDataDirectory $TerminalDataDirectory -TerminalPath $TerminalPath -ConfigurationPath $ConfigurationPath -Symbols @($Symbol))|ConvertFrom-Json)
function Hash([string]$Path){(Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()}
function Acl([string]$Path){$a=Get-Acl -LiteralPath $Path;[ordered]@{owner=$a.Owner;sddl=$a.Sddl}}
function Relative([string]$Path){$Path.Substring($scope.server_namespace_path.Length).TrimStart('\').Replace('\','/')}
$objects=@();foreach($root in @($scope.symbol_roots)){if(!$root.exists){throw 'missing required server-scoped cache root'};foreach($item in @((Get-Item -LiteralPath $root.canonical_path -Force))+@(Get-ChildItem -LiteralPath $root.canonical_path -Force -Recurse|Sort-Object FullName)){if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'reparse point rejected in environment collection'};$type=if($item.PSIsContainer){'directory'}else{'file'};$objects+=[ordered]@{path=Relative $item.FullName;absolute_canonical_path=[IO.Path]::GetFullPath($item.FullName);object_type=$type;size=if($type-eq'file'){[int64]$item.Length}else{$null};creation_utc=$item.CreationTimeUtc.ToString('o');last_write_utc=$item.LastWriteTimeUtc.ToString('o');sha256=if($type-eq'file'){Hash $item.FullName}else{$null};acl=Acl $item.FullName;reparse_point=$false;symbol=$root.symbol;cache_kind=$root.kind}}}
$files=@($objects|Where-Object{$_.object_type-eq'file'});if($files.Count-eq 0){throw 'empty relevant server-scoped cache inventory'}
$record=[ordered]@{schema_version='nora.ten_strategy_environment_inventory_v3';phase=$Phase;server_scope=$scope;observed_bar_count=$ObservedBarCount;earliest_history_timestamp=$EarliestHistoryTimestamp;latest_history_timestamp=$LatestHistoryTimestamp;objects=$objects;files=$files}
$record|ConvertTo-Json -Depth 24|Set-Content -LiteralPath $Destination -Encoding utf8
