param(
 [Parameter(Mandatory=$true)][ValidateSet('enable','status','cleanup')][string]$Action,
 [Parameter(Mandatory=$true)][string]$CampaignId,
 [Parameter(Mandatory=$true)][string]$EvidenceRoot,
 [string]$InstallRoot='C:\Program Files\Darwinex MetaTrader 5'
)
$ErrorActionPreference='Stop'
$schema='nora.phase2_mt5_network_containment_v1'
if($CampaignId -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$'){throw 'invalid containment identity'}
if(!(Test-Path -LiteralPath $EvidenceRoot -PathType Container)){throw 'missing evidence root'}
function Hash([string]$Path){(Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()}
function AtomicJson([string]$Path,$Value){$tmp=$Path+'.partial.'+[guid]::NewGuid().ToString('N');$Value|ConvertTo-Json -Depth 12 -Compress|Set-Content -LiteralPath $tmp -Encoding utf8 -NoNewline;Move-Item -LiteralPath $tmp -Destination $Path}
function Identity(){ $i=[Security.Principal.WindowsIdentity]::GetCurrent();[ordered]@{name=$i.Name;sid=$i.User.Value} }
function Executables(){
 $terminal=Join-Path $InstallRoot 'terminal64.exe'
 if(!(Test-Path -LiteralPath $terminal -PathType Leaf)){throw 'missing terminal executable'}
 $agents=@(Get-ChildItem -LiteralPath $InstallRoot -Filter metatester64.exe -File -Recurse -ErrorAction Stop|Sort-Object FullName)
 if($agents.Count -eq 0){throw 'missing metatester executable'}
 @($terminal)+@($agents.FullName)
}
function Group(){'NoraPhase2Containment-'+$CampaignId}
function RuleName([int]$Index){'NoraPhase2Containment-'+$CampaignId+'-'+$Index}
function Rules(){@(Get-NetFirewallRule -Group (Group) -ErrorAction SilentlyContinue|Sort-Object Name)}
function RuleView(){
 @((Rules)|ForEach-Object{
   $rule=$_;$app=@(Get-NetFirewallApplicationFilter -AssociatedNetFirewallRule $rule -ErrorAction Stop)
   if($app.Count-ne 1){throw 'ambiguous firewall application filter'}
   [ordered]@{name=$rule.Name;instance_id=$rule.InstanceID;display_name=$rule.DisplayName;group=$rule.Group;enabled=[string]$rule.Enabled;direction=[string]$rule.Direction;action=[string]$rule.Action;profile=[string]$rule.Profile;program=$app[0].Program}
 })
}
function AssertNoContradictoryAllow([string[]]$Paths){
 $allows=@(Get-NetFirewallRule -Direction Outbound -Enabled True -Action Allow -ErrorAction Stop|ForEach-Object{
   $rule=$_;Get-NetFirewallApplicationFilter -AssociatedNetFirewallRule $rule -ErrorAction SilentlyContinue|ForEach-Object{[ordered]@{rule=$rule.Name;program=$_.Program}}
 })
 foreach($path in $Paths){if(@($allows|Where-Object{$_.program -eq $path}).Count){throw 'contradictory MT5 outbound allow rule'}}
}
function State(){
 $paths=@(Executables);$rules=@(RuleView);$connections=@()
 foreach($process in @(Get-Process terminal64,metatester64 -ErrorAction SilentlyContinue)){
   $connections+=@(Get-NetTCPConnection -OwningProcess $process.Id -ErrorAction SilentlyContinue|Where-Object{$_.RemoteAddress -notin @('127.0.0.1','::1','0.0.0.0','::')}|ForEach-Object{[ordered]@{pid=$process.Id;process=$process.ProcessName;state=[string]$_.State;local_address=$_.LocalAddress;local_port=$_.LocalPort;remote_address=$_.RemoteAddress;remote_port=$_.RemotePort}})
 }
 [ordered]@{schema_version=$schema;campaign_identity=$CampaignId;group=(Group);captured_utc=(Get-Date).ToUniversalTime().ToString('o');creator=Identity;executables=@($paths|ForEach-Object{[ordered]@{path=$_;sha256=Hash $_}});rules=$rules;active_rule_count=$rules.Count;observed_mt5_connections=$connections}
}
switch($Action){
 'enable' {
   $paths=@(Executables);if((Rules).Count-ne 0){throw 'stale containment rules exist'};AssertNoContradictoryAllow $paths
   $index=0;foreach($path in $paths){$index++;New-NetFirewallRule -Name (RuleName $index) -DisplayName (RuleName $index) -Group (Group) -Direction Outbound -Action Block -Program $path -RemoteAddress Any -Profile Any -Enabled True|Out-Null}
   $state=State;if($state.active_rule_count-ne$paths.Count){throw 'containment rule count mismatch'}
   foreach($rule in $state.rules){if($rule.direction-ne'Outbound' -or $rule.action-ne'Block' -or $rule.enabled-ne'True' -or $rule.profile-ne'Any'){throw 'containment rule not active'}}
   AtomicJson (Join-Path $EvidenceRoot ('containment-'+$CampaignId+'.json')) $state;$state|ConvertTo-Json -Depth 12 -Compress
 }
 'status' {
   $state=State;$expected=@(Executables).Count;if($state.active_rule_count-ne$expected){throw 'containment absent or incomplete'};foreach($rule in $state.rules){if($rule.direction-ne'Outbound' -or $rule.action-ne'Block' -or $rule.enabled-ne'True' -or $rule.profile-ne'Any'){throw 'containment rule not active'}};$state|ConvertTo-Json -Depth 12 -Compress
 }
 'cleanup' {
   $before=@(Rules);if($before.Count-eq 0){throw 'no containment rules to clean'};foreach($rule in $before){Remove-NetFirewallRule -Name $rule.Name -ErrorAction Stop};if((Rules).Count-ne 0){throw 'containment cleanup incomplete'};$result=[ordered]@{schema_version=$schema;campaign_identity=$CampaignId;group=(Group);cleanup='pass';removed_rule_count=$before.Count;removed_rules=$before;completed_utc=(Get-Date).ToUniversalTime().ToString('o');creator=Identity};AtomicJson (Join-Path $EvidenceRoot ('containment-'+$CampaignId+'-cleanup.json')) $result;$result|ConvertTo-Json -Depth 12 -Compress
 }
}
