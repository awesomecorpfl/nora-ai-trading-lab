param(
 [Parameter(Mandatory=$true)][string]$TerminalDataDirectory,
 [Parameter(Mandatory=$true)][string]$TerminalPath,
 [Parameter(Mandatory=$true)][string]$ConfigurationPath,
 [Parameter(Mandatory=$true)][string[]]$Symbols
)
$ErrorActionPreference='Stop'
$schema='nora.phase2_mt5_server_scoped_cache_v2'
function Hash([string]$Path){(Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()}
function Canonical([string]$Path){[IO.Path]::GetFullPath($Path).TrimEnd('\')}
function SamePath([string]$Left,[string]$Right){[string]::Equals((Canonical $Left),(Canonical $Right),[StringComparison]::OrdinalIgnoreCase)}
function Under([string]$Child,[string]$Parent){$p=(Canonical $Parent)+'\';(Canonical $Child).StartsWith($p,[StringComparison]::OrdinalIgnoreCase)}
function NoReparse([string]$Path){$item=Get-Item -LiteralPath $Path -Force;if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'reparse point rejected: '+$Path};$item}
function CanonicalJson($Value){$Value|ConvertTo-Json -Depth 20 -Compress}
function BytesHash([string]$Text){([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($Text))).Replace('-','').ToLowerInvariant())}
if($Symbols.Count -eq 0 -or @($Symbols|Where-Object{$_ -notin @('GDAXI','AUDCAD')}).Count){throw 'invalid campaign symbols'}
$data=NoReparse $TerminalDataDirectory;$terminal=NoReparse $TerminalPath;$config=NoReparse $ConfigurationPath
$originPath=Join-Path $data.FullName 'origin.txt';if(!(Test-Path -LiteralPath $originPath -PathType Leaf)){throw 'missing terminal origin binding'}
$origin=(Get-Content -LiteralPath $originPath -Raw).Trim();if(!$origin -or !(SamePath $origin (Split-Path -Parent $terminal.FullName))){throw 'terminal data directory origin mismatch'}
$raw=Get-Content -LiteralPath $config.FullName -Raw
$servers=@([regex]::Matches($raw,'(?m)^Server=([^\r\n]+)$')|ForEach-Object{$_.Groups[1].Value.Trim()})
if($servers.Count -ne 1){throw 'ambiguous or missing tester server identity'};$server=$servers[0]
if($server -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$'){throw 'unsafe tester server identity'}
$bases=Join-Path $data.FullName 'Bases';NoReparse $bases|Out-Null
$matches=@(Get-ChildItem -LiteralPath $bases -Directory -Force|Where-Object{[string]::Equals($_.Name,$server,[StringComparison]::OrdinalIgnoreCase)})
if($matches.Count -ne 1){throw 'ambiguous or missing server namespace'};$namespace=NoReparse $matches[0].FullName
if(!(Under $namespace.FullName $bases)){throw 'server namespace escapes terminal Bases'}
$roots=@();foreach($symbol in $Symbols|Sort-Object -Unique){foreach($kind in @('history','ticks')){$path=Join-Path $namespace.FullName ($kind+'\'+$symbol);if(Test-Path -LiteralPath $path){$item=NoReparse $path;if(!(Under $item.FullName $namespace.FullName)){throw 'symbol root escapes server namespace'};$roots+=[ordered]@{symbol=$symbol;kind=$kind;exists=$true;canonical_path=(Canonical $item.FullName)}}else{$roots+=[ordered]@{symbol=$symbol;kind=$kind;exists=$false;canonical_path=(Canonical $path)}}}}
$value=[ordered]@{schema_version=$schema;terminal_data_directory=(Canonical $data.FullName);terminal_instance_id=$data.Name;terminal_origin_path=(Canonical $origin);terminal_path=(Canonical $terminal.FullName);terminal_sha256=Hash $terminal.FullName;terminal_version=$terminal.VersionInfo.FileVersion;configuration_path=(Canonical $config.FullName);configuration_sha256=Hash $config.FullName;broker_server_identity=$server;server_namespace_observed=$namespace.Name;server_namespace_path=(Canonical $namespace.FullName);bases_path=(Canonical $bases);symbol_roots=$roots}
$binding=[ordered]@{terminal_data_directory=$value.terminal_data_directory;terminal_instance_id=$value.terminal_instance_id;terminal_origin_path=$value.terminal_origin_path;terminal_path=$value.terminal_path;terminal_sha256=$value.terminal_sha256;broker_server_identity=$value.broker_server_identity;server_namespace_observed=$value.server_namespace_observed;server_namespace_path=$value.server_namespace_path;bases_path=$value.bases_path;symbol_roots=$value.symbol_roots};$value.server_binding_identity=BytesHash (CanonicalJson $binding);$value.server_scope_identity=BytesHash (CanonicalJson $value);$value|ConvertTo-Json -Depth 20 -Compress
