param(
 [Parameter(Mandatory=$true)][string]$TerminalDataDirectory,
 [Parameter(Mandatory=$true)][string]$TerminalPath,
 [Parameter(Mandatory=$true)][string]$ConfigurationPath,
 [Parameter(Mandatory=$true)][string[]]$Symbols,
 [Parameter(Mandatory=$true)][string]$ResolverPath,
 [Parameter(Mandatory=$true)][string]$Destination
)
$ErrorActionPreference='Stop';$schema='nora.phase2_mt5_cache_inventory_v2'
function Hash([string]$Path){(Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()}
function AtomicJson([string]$Path,$Value){$tmp=$Path+'.partial.'+[guid]::NewGuid().ToString('N');$Value|ConvertTo-Json -Depth 24 -Compress|Set-Content -LiteralPath $tmp -Encoding utf8 -NoNewline;Move-Item -LiteralPath $tmp -Destination $Path}
function Canonical([string]$Path){[IO.Path]::GetFullPath($Path).TrimEnd('\')}
function Relative([string]$Path,[string]$Root){$Path.Substring((Canonical $Root).Length).TrimStart('\').Replace('\','/')}
function Acl([string]$Path){$a=Get-Acl -LiteralPath $Path;[ordered]@{owner=$a.Owner;sddl=$a.Sddl}}
function Metadata($Item,[string]$Symbol,[string]$Kind){$year=$null;if($Item.Name -match '^(19|20)\d{2}\.hcc$'){$year=[int]$Item.BaseName};[ordered]@{symbol=$Symbol;cache_kind=$Kind;filename_year_candidate=$year;parse_status=if($year-ne$null){'filename_year_candidate_only'}else{'unsupported_binary_or_non-year_name'}}}
function Identity($Value){$json=$Value|ConvertTo-Json -Depth 24 -Compress;([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($json))).Replace('-','').ToLowerInvariant())}
if(!(Test-Path -LiteralPath $ResolverPath -PathType Leaf)){throw 'missing server scope resolver'}
$scope=((& $ResolverPath -TerminalDataDirectory $TerminalDataDirectory -TerminalPath $TerminalPath -ConfigurationPath $ConfigurationPath -Symbols $Symbols)|ConvertFrom-Json)
$objects=@();$relevantFiles=0
foreach($root in @($scope.symbol_roots)){
 if(!$root.exists){$objects+=[ordered]@{relative_path=(($root.kind+'/'+$root.symbol));absolute_canonical_path=$root.canonical_path;object_type='missing_directory';size=$null;creation_utc=$null;last_write_utc=$null;sha256=$null;acl=$null;reparse_point=$false;metadata=[ordered]@{symbol=$root.symbol;cache_kind=$root.kind;parse_status='missing'}};continue}
 $members=@(Get-ChildItem -LiteralPath $root.canonical_path -Force -Recurse|Sort-Object FullName)
 foreach($item in @((Get-Item -LiteralPath $root.canonical_path -Force))+$members){if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'reparse point rejected in cache inventory: '+$item.FullName};$type=if($item.PSIsContainer){'directory'}else{'file'};if($type-eq'file'){$relevantFiles++};$objects+=[ordered]@{relative_path=Relative $item.FullName $scope.server_namespace_path;absolute_canonical_path=Canonical $item.FullName;object_type=$type;size=if($type-eq'file'){[int64]$item.Length}else{$null};creation_utc=$item.CreationTimeUtc.ToString('o');last_write_utc=$item.LastWriteTimeUtc.ToString('o');sha256=if($type-eq'file'){Hash $item.FullName}else{$null};acl=Acl $item.FullName;reparse_point=$false;metadata=Metadata $item $root.symbol $root.kind}
 }
}
$record=[ordered]@{schema_version=$schema;captured_utc=(Get-Date).ToUniversalTime().ToString('o');server_scope=$scope;objects=$objects;relevant_file_count=$relevantFiles;empty_relevant_inventory=($relevantFiles-eq 0)};$record.inventory_identity=Identity $record
AtomicJson $Destination $record;$record|ConvertTo-Json -Depth 24 -Compress
