[CmdletBinding()]
param(
 [Parameter(Mandatory=$true)][ValidateSet('capture','verify','smoke')][string]$Mode,
 [string]$DestinationPath,
 [string]$InventoryPath,
 [string]$ExpectedSha256,
 [Parameter(Mandatory=$true)][string]$RepositoryCommit,
 [string]$EvidenceRoot='C:\NoraEvidence\Phase2'
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$schema='nora.phase2_firewall_inventory_v1'
function Hash([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
function Values($v){@($v|ForEach-Object{[string]$_}|Where-Object{![string]::IsNullOrWhiteSpace($_)}|Sort-Object -Unique)}
function OneFilter($rule,[string]$cmd){$v=@(& $cmd -AssociatedNetFirewallRule $rule -ErrorAction Stop);if($v.Count-ne1){throw ('ambiguous filter association: '+$cmd)};return $v[0]}
function Rules([string]$store,[string]$view){
 @(Get-NetFirewallRule -PolicyStore $store -ErrorAction Stop|ForEach-Object{
  $r=$_;$app=OneFilter $r 'Get-NetFirewallApplicationFilter';$svc=OneFilter $r 'Get-NetFirewallServiceFilter';$port=OneFilter $r 'Get-NetFirewallPortFilter';$addr=OneFilter $r 'Get-NetFirewallAddressFilter';$iface=OneFilter $r 'Get-NetFirewallInterfaceTypeFilter';$sec=OneFilter $r 'Get-NetFirewallSecurityFilter'
  [ordered]@{view=$view;name=[string]$r.Name;instance_id=[string]$r.InstanceID;display_name=[string]$r.DisplayName;group=[string]$r.Group;description=[string]$r.Description;enabled=([string]$r.Enabled-eq'True');direction=[string]$r.Direction;action=[string]$r.Action;profile=[string]$r.Profile;policy_store=$store;policy_store_source_type=[string]$r.PolicyStoreSourceType;policy_store_source=[string]$r.PolicyStoreSource;edge_traversal=[string]$r.EdgeTraversalPolicy;interface_types=Values $iface.InterfaceType;owner=[string]$r.Owner;programs=Values $app.Program;services=Values $svc.Service;protocols=Values $port.Protocol;local_ports=Values $port.LocalPort;remote_ports=Values $port.RemotePort;icmp_types=Values $port.IcmpType;local_addresses=Values $addr.LocalAddress;remote_addresses=Values $addr.RemoteAddress;interfaces=@();security=Values @($sec.Authentication,$sec.Encryption,$sec.OverrideBlockRules);packages=Values @($app.Package);local_users=Values @($sec.LocalUser);remote_users=Values @($sec.RemoteUser);diagnostics=[ordered]@{status=[string]$r.Status;status_code=[string]$r.StatusCode;primary_status=[string]$r.PrimaryStatus;enforcement_status=[string]$r.EnforcementStatus}}
 }|Sort-Object view,policy_store_source_type,policy_store_source,instance_id,name)
}
function Profiles(){@(Get-NetFirewallProfile -PolicyStore ActiveStore -ErrorAction Stop|ForEach-Object{[ordered]@{name=[string]$_.Name;enabled=[bool]$_.Enabled;default_inbound=[string]$_.DefaultInboundAction;default_outbound=[string]$_.DefaultOutboundAction;allow_local_firewall_rules=[string]$_.AllowLocalFirewallRules;allow_local_ipsec_rules=[string]$_.AllowLocalIPsecRules;notify_on_listen=[string]$_.NotifyOnListen;policy_store_source=[string]$_.PolicyStoreSource}}|Sort-Object name)}
if($RepositoryCommit-notmatch'^[0-9a-f]{40}$'){throw 'invalid repository commit'}
if($Mode-eq'smoke'){$p=Profiles;if($p.Count-ne3){throw 'profile capture incomplete'};[ordered]@{schema='nora.phase2_firewall_capture_smoke_v1';mutation_cmdlets_invoked=$false;profile_count=$p.Count}|ConvertTo-Json -Compress;exit 0}
if($Mode-eq'verify'){$full=[IO.Path]::GetFullPath($InventoryPath);$root=[IO.Path]::GetFullPath($EvidenceRoot).TrimEnd('\');if(!$full.StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'inventory outside evidence root'};if((Hash $full)-ne$ExpectedSha256.ToLowerInvariant()){throw 'inventory hash mismatch'};$v=Get-Content -LiteralPath $full -Raw|ConvertFrom-Json;if($v.schema_version-ne$schema-or@($v.profiles).Count-ne3){throw 'inventory schema or profile mismatch'};[ordered]@{verdict='PASS';path=$full;size=(Get-Item $full).Length;sha256=Hash $full}|ConvertTo-Json -Compress;exit 0}
$dest=[IO.Path]::GetFullPath($DestinationPath);$root=[IO.Path]::GetFullPath($EvidenceRoot).TrimEnd('\');if(!$dest.StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'inventory outside evidence root'}
$value=[ordered]@{schema_version=$schema;host_identity=[Security.Principal.WindowsIdentity]::GetCurrent().Name;repository_commit=$RepositoryCommit;captured_utc=(Get-Date).ToUniversalTime().ToString('o');profiles=Profiles;effective_rules=Rules 'ActiveStore' 'effective';persistent_rules=Rules 'PersistentStore' 'persistent';diagnostics=[ordered]@{excluded_from_semantic_digest=@('captured_utc','display_name','description','diagnostics.status','diagnostics.status_code','diagnostics.primary_status','diagnostics.enforcement_status');capture_tool_path=$PSCommandPath;capture_tool_sha256=Hash $PSCommandPath}}
$json=$value|ConvertTo-Json -Depth 20 -Compress;$parent=Split-Path -Parent $dest;New-Item -ItemType Directory -Force -Path $parent|Out-Null;$tmp=$dest+'.partial.'+[guid]::NewGuid().ToString('N');[IO.File]::WriteAllText($tmp,$json,[Text.UTF8Encoding]::new($false));$s=[IO.File]::Open($tmp,'Open','ReadWrite','None');$s.Flush($true);$s.Dispose();if(Test-Path -LiteralPath $dest){if((Hash $dest)-ne(Hash $tmp)){throw 'conflicting inventory publication'};Remove-Item $tmp -Force}else{[IO.File]::Move($tmp,$dest)};[ordered]@{path=$dest;size=(Get-Item $dest).Length;sha256=Hash $dest}|ConvertTo-Json -Compress
