[CmdletBinding()]
param(
 [Parameter(Mandatory=$true)][ValidateSet('stage','verify','status','recover','cleanup')][string]$Action,
 [Parameter(Mandatory=$true)][string]$CampaignId,
 [Parameter(Mandatory=$true)][string]$EvidenceRoot,
 [string]$InstallRoot='C:\Program Files\Darwinex MetaTrader 5',
 [string[]]$ExecutablePath,
 [ValidateSet('none','before_rules','after_first_rule','after_all_rules_before_final','after_final_before_accept')][string]$Fault='none'
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$schema='nora.phase2_mt5_network_containment_transaction_v2'
if($CampaignId -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$'){throw 'invalid containment identity'}
if(!(Test-Path -LiteralPath $EvidenceRoot -PathType Container)){throw 'missing evidence root'}
function Hash([string]$Path){(Get-FileHash -Algorithm SHA256 -LiteralPath $Path -ErrorAction Stop).Hash.ToLowerInvariant()}
function AtomicJson([string]$Path,$Value){$tmp=$Path+'.partial.'+[guid]::NewGuid().ToString('N');[IO.File]::WriteAllText($tmp,($Value|ConvertTo-Json -Depth 20 -Compress),[Text.UTF8Encoding]::new($false));if(Test-Path -LiteralPath $Path){$backup=$Path+'.replace-backup.'+[guid]::NewGuid().ToString('N');[IO.File]::Replace($tmp,$Path,$backup);Remove-Item -LiteralPath $backup -Force}else{[IO.File]::Move($tmp,$Path)}}
function Identity(){ $i=[Security.Principal.WindowsIdentity]::GetCurrent();[ordered]@{name=$i.Name;sid=$i.User.Value} }
function Get-NoraContainmentGroup {
 param([Parameter(Mandatory=$true)][string]$RunId)
 $value='NoraPhase2Containment-'+$RunId
 if($value -isnot [string] -or [string]::IsNullOrWhiteSpace($value)){throw 'Containment firewall group resolved to null or empty.'}
 if($value -notmatch '^NoraPhase2Containment-[A-Za-z0-9][A-Za-z0-9._-]{2,127}$' -or $value.Length -gt 255 -or $value -match '[\x00-\x1f;&|]'){throw 'Containment firewall group resolved to invalid value.'}
 return [string]$value
}
$firewallGroup=Get-NoraContainmentGroup -RunId $CampaignId
if([string]::IsNullOrWhiteSpace($firewallGroup)){throw 'Containment firewall group resolved to null or empty.'}
function RuleName([int]$Index){$firewallGroup+'-'+$Index}
function IntentPath(){Join-Path $EvidenceRoot ('containment-'+$CampaignId+'.intent.json')}
function FinalPath(){Join-Path $EvidenceRoot ('containment-'+$CampaignId+'.json')}
function AcceptedPath(){Join-Path $EvidenceRoot ('containment-'+$CampaignId+'.transaction-accepted.json')}
function FailurePath(){Join-Path $EvidenceRoot ('containment-'+$CampaignId+'.transaction-failure.json')}
function RecoveryPath(){Join-Path $EvidenceRoot ('containment-'+$CampaignId+'.transaction-recovery.json')}
function Bindings(){
 $paths=if($ExecutablePath -and $ExecutablePath.Count){@($ExecutablePath)}else{@((Join-Path $InstallRoot 'terminal64.exe'))+@(Get-ChildItem -LiteralPath $InstallRoot -Filter metatester64.exe -File -Recurse -ErrorAction Stop|Sort-Object FullName|ForEach-Object{$_.FullName})}
 if(!$paths.Count){throw 'missing containment executables'}
 $seen=@{};$result=@();foreach($path in $paths){if([string]::IsNullOrWhiteSpace($path) -or !(Test-Path -LiteralPath $path -PathType Leaf)){throw 'missing containment executable'};$canonical=[IO.Path]::GetFullPath($path);if($seen.ContainsKey($canonical.ToLowerInvariant())){throw 'duplicate containment executable'};$seen[$canonical.ToLowerInvariant()]=$true;$result+=[ordered]@{path=$canonical;sha256=Hash $canonical}}
 return @($result)
}
function Rules(){@(Get-NetFirewallRule -Group $firewallGroup -ErrorAction SilentlyContinue|Sort-Object Name)}
function RuleView(){@((Rules)|ForEach-Object{$rule=$_;$apps=@(Get-NetFirewallApplicationFilter -AssociatedNetFirewallRule $rule -ErrorAction Stop);if($apps.Count-ne1){throw 'ambiguous firewall application filter'};[ordered]@{name=$rule.Name;instance_id=[string]$rule.InstanceID;display_name=$rule.DisplayName;group=$rule.Group;enabled=[string]$rule.Enabled;direction=[string]$rule.Direction;action=[string]$rule.Action;profile=[string]$rule.Profile;program=$apps[0].Program}})}
function AllRuleIdentity(){ $v=@(Get-NetFirewallRule -ErrorAction Stop|Sort-Object Name|ForEach-Object{[ordered]@{name=$_.Name;enabled=[string]$_.Enabled;direction=[string]$_.Direction;action=[string]$_.Action;profile=[string]$_.Profile;group=$_.Group}});$b=[Text.Encoding]::UTF8.GetBytes(($v|ConvertTo-Json -Depth 10 -Compress));([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash($b))).Replace('-','').ToLowerInvariant() }
function AssertNoContradictoryAllow($bindings){$allows=@(Get-NetFirewallRule -Direction Outbound -Enabled True -Action Allow -ErrorAction Stop|ForEach-Object{$r=$_;Get-NetFirewallApplicationFilter -AssociatedNetFirewallRule $r -ErrorAction SilentlyContinue|ForEach-Object{[string]$_.Program}});foreach($binding in $bindings){if($allows -contains $binding.path){throw 'contradictory MT5 outbound allow rule'}}}
function State($bindings){$connections=@();foreach($process in @(Get-Process terminal64,metatester64 -ErrorAction SilentlyContinue)){$connections+=@(Get-NetTCPConnection -OwningProcess $process.Id -ErrorAction SilentlyContinue|Where-Object{$_.RemoteAddress-notin@('127.0.0.1','::1','0.0.0.0','::')}|ForEach-Object{[ordered]@{pid=$process.Id;process=$process.ProcessName;remote_address=$_.RemoteAddress;remote_port=$_.RemotePort;state=[string]$_.State}})};[ordered]@{schema_version=$schema;campaign_identity=$CampaignId;group=$firewallGroup;captured_utc=(Get-Date).ToUniversalTime().ToString('o');creator=Identity;executables=$bindings;rules=@(RuleView);active_rule_count=@(Rules).Count;observed_mt5_connections=$connections;unrelated_firewall_population_identity=AllRuleIdentity}}
function VerifyState($state){
 if($state.schema_version-ne$schema -or $state.campaign_identity-ne$CampaignId -or $state.group-ne$firewallGroup){throw 'containment record identity mismatch'}
 $bindings=@(Bindings);if(@($state.executables).Count-ne$bindings.Count -or @($state.rules).Count-ne$bindings.Count){throw 'containment cardinality mismatch'}
 AssertNoContradictoryAllow $bindings
 for($i=0;$i-lt$bindings.Count;$i++){ $binding=$bindings[$i];$rule=@($state.rules|Where-Object{$_.name-eq(RuleName ($i+1))});if($rule.Count-ne1){throw 'missing or duplicate rule GUID binding'};if($rule[0].instance_id-ne(@(RuleView|Where-Object{$_.name-eq$rule[0].name})[0].instance_id)){throw 'rule GUID mismatch'};if($rule[0].program-ne$binding.path -or $state.executables[$i].path-ne$binding.path -or $state.executables[$i].sha256-ne$binding.sha256){throw 'rule application path or hash mismatch'};if($rule[0].enabled-ne'True' -or $rule[0].direction-ne'Outbound' -or $rule[0].action-ne'Block' -or $rule[0].profile-ne'Any'){throw 'containment rule not active'} }
 return $true
}
function Failure([string]$Reason,[string]$Message){$bindings=$null;try{$bindings=Bindings}catch{};$ruleCount=@(Rules).Count;$classification=if($ruleCount-eq0){'NO_RULES_TRANSACTION_FAILED'}else{'RULES_PRESENT_RECORD_INCOMPLETE'};$v=[ordered]@{schema_version=$schema;campaign_identity=$CampaignId;classification=$classification;accepted=$false;reason=$Reason;message=$Message;intent_path=IntentPath;final_record_path=FinalPath;active_rule_count=$ruleCount;executables=$bindings;captured_utc=(Get-Date).ToUniversalTime().ToString('o');creator=Identity};AtomicJson (FailurePath) $v;return $v}
function FreshVerify(){ $args=@('-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',$PSCommandPath,'-Action','verify','-CampaignId',$CampaignId,'-EvidenceRoot',$EvidenceRoot,'-InstallRoot',$InstallRoot);foreach($p in @($ExecutablePath)){$args+=@('-ExecutablePath',$p)};$output=@(& powershell.exe @args 2>&1);if($LASTEXITCODE-ne0){throw ('fresh record validation failed: '+($output -join "`n"))};return ($output -join "`n")}
try {
 switch($Action){
  'stage' {
   $bindings=Bindings;$intent=[ordered]@{schema_version=$schema;phase='intent_prepared';campaign_identity=$CampaignId;repository_commit=$env:NORA_REPOSITORY_COMMIT;creator=Identity;executables=$bindings;group=$firewallGroup;intended_rule_names=@(for($i=1;$i-le$bindings.Count;$i++){RuleName $i});intended_final_record_path=FinalPath;evidence_root=$EvidenceRoot;captured_utc=(Get-Date).ToUniversalTime().ToString('o')}
   if(Test-Path -LiteralPath (AcceptedPath)){& $PSCommandPath -Action verify -CampaignId $CampaignId -EvidenceRoot $EvidenceRoot -InstallRoot $InstallRoot -ExecutablePath $ExecutablePath;break}
   if(((Rules).Count -ne 0) -or (Test-Path -LiteralPath (IntentPath))){throw 'stale or incomplete containment transaction requires recovery'}
   AtomicJson (IntentPath) $intent
   $pre=[ordered]@{phase='pre_state_captured';unrelated_firewall_population_identity=AllRuleIdentity;captured_utc=(Get-Date).ToUniversalTime().ToString('o')}
   if($Fault-eq'before_rules'){throw 'forced failure before rules'}
   AssertNoContradictoryAllow $bindings;$i=0;foreach($binding in $bindings){$i++;New-NetFirewallRule -Name (RuleName $i) -DisplayName (RuleName $i) -Group $firewallGroup -Direction Outbound -Action Block -Program $binding.path -RemoteAddress Any -Profile Any -Enabled True -ErrorAction Stop|Out-Null;if($Fault-eq'after_first_rule' -and $i-eq1){throw 'forced failure after first rule'}}
   $state=State $bindings;$state.phase='rules_verified';$state.rules_created_utc=(Get-Date).ToUniversalTime().ToString('o');$state.pre_state=$pre;VerifyState $state|Out-Null
   if($Fault-eq'after_all_rules_before_final'){throw 'forced failure after all rules before final publication'}
   $state.phase='final_record_published';AtomicJson (FinalPath) $state
   if($Fault-eq'after_final_before_accept'){throw 'forced failure after final publication'}
   FreshVerify|Out-Null
   $accepted=[ordered]@{schema_version=$schema;phase='transaction_accepted';verification_phase='final_record_reopened';campaign_identity=$CampaignId;intent_sha256=Hash (IntentPath);final_record_path=FinalPath;final_record_sha256=Hash (FinalPath);accepted_utc=(Get-Date).ToUniversalTime().ToString('o');creator=Identity};AtomicJson (AcceptedPath) $accepted
   $accepted|ConvertTo-Json -Depth 20 -Compress
  }
  'verify' {if(!(Test-Path -LiteralPath (FinalPath)) -or !(Test-Path -LiteralPath (AcceptedPath))){throw 'missing accepted containment records'};$state=Get-Content -LiteralPath (FinalPath) -Raw|ConvertFrom-Json;VerifyState $state|Out-Null;$accepted=Get-Content -LiteralPath (AcceptedPath) -Raw|ConvertFrom-Json;if($accepted.phase-ne'transaction_accepted' -or $accepted.final_record_sha256-ne(Hash (FinalPath))){throw 'accepted transaction binding mismatch'};$state|ConvertTo-Json -Depth 20 -Compress}
  'status' {& $PSCommandPath -Action verify -CampaignId $CampaignId -EvidenceRoot $EvidenceRoot -InstallRoot $InstallRoot -ExecutablePath $ExecutablePath}
  'recover' {$count=@(Rules).Count;$classification=if($count-eq0 -and !(Test-Path -LiteralPath (IntentPath))){'NO_RULES_NO_RECORD'}elseif($count-eq0){'NO_RULES_TRANSACTION_FAILED'}elseif(!(Test-Path -LiteralPath (FinalPath))){'RULES_PRESENT_RECORD_INCOMPLETE'}else{'RECORD_PRESENT_REQUIRES_VERIFY'};$v=[ordered]@{schema_version=$schema;campaign_identity=$CampaignId;classification=$classification;active_rule_count=$count;intent_present=(Test-Path -LiteralPath (IntentPath));final_record_present=(Test-Path -LiteralPath (FinalPath));accepted_record_present=(Test-Path -LiteralPath (AcceptedPath));recovered_utc=(Get-Date).ToUniversalTime().ToString('o')};AtomicJson (RecoveryPath) $v;$v|ConvertTo-Json -Depth 20 -Compress}
  'cleanup' {$before=State (Bindings);$rules=@(Rules);foreach($rule in $rules){Remove-NetFirewallRule -Name $rule.Name -ErrorAction Stop};if(@(Rules).Count-ne0){throw 'containment cleanup incomplete'};$after=AllRuleIdentity;$v=[ordered]@{schema_version=$schema;campaign_identity=$CampaignId;cleanup='pass';removed_rule_count=$rules.Count;unrelated_rules_before_sha256=$before.unrelated_firewall_population_identity;unrelated_rules_after_sha256=$after;unrelated_rules_unchanged=($before.unrelated_firewall_population_identity-eq$after);completed_utc=(Get-Date).ToUniversalTime().ToString('o')};if(!$v.unrelated_rules_unchanged){throw 'unrelated firewall rules changed during cleanup'};AtomicJson (Join-Path $EvidenceRoot ('containment-'+$CampaignId+'-cleanup.json')) $v;$v|ConvertTo-Json -Depth 20 -Compress}
 }
} catch {Failure $_.Exception.GetType().FullName $_.Exception.Message|Out-Null;[Console]::Error.WriteLine($_.Exception.Message);exit 1}
