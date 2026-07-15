[CmdletBinding()]
param(
 [Parameter(Mandatory=$true)][ValidateSet('stage','verify','verify-final','status','recover','cleanup','smoke')][string]$Action,
 [Parameter(Mandatory=$true)][string]$CampaignId,
 [Parameter(Mandatory=$true)][string]$EvidenceRoot,
 [string]$InstallRoot='C:\Program Files\Darwinex MetaTrader 5',
 [string[]]$ExecutablePath,
 [ValidateSet('none','before_rules','after_first_rule','after_all_rules_before_final','after_final_before_accept')][string]$Fault='none'
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$schema='nora.phase2_mt5_network_containment_transaction_v3'
if($CampaignId -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$'){throw 'invalid containment identity'}
if(!(Test-Path -LiteralPath $EvidenceRoot -PathType Container)){throw 'missing evidence root'}
function Hash([string]$Path){(Get-FileHash -Algorithm SHA256 -LiteralPath $Path -ErrorAction Stop).Hash.ToLowerInvariant()}
function AtomicJson([string]$Path,$Value){$tmp=$Path+'.partial.'+[guid]::NewGuid().ToString('N');[IO.File]::WriteAllText($tmp,($Value|ConvertTo-Json -Depth 20 -Compress),[Text.UTF8Encoding]::new($false));if(Test-Path -LiteralPath $Path){$backup=$Path+'.replace-backup.'+[guid]::NewGuid().ToString('N');[IO.File]::Replace($tmp,$Path,$backup);Remove-Item -LiteralPath $backup -Force}else{[IO.File]::Move($tmp,$Path)}}
function Identity(){ $i=[Security.Principal.WindowsIdentity]::GetCurrent();[ordered]@{name=$i.Name;sid=$i.User.Value} }
function Normalize-NoraExecutablePaths {
 param([Parameter(Mandatory=$true)][bool]$WasBound,[object]$RawPaths,[Parameter(Mandatory=$true)][string]$Root)
 [object[]]$items=if($WasBound){@($RawPaths)}else{@((Join-Path $Root 'terminal64.exe'))+@(Get-ChildItem -LiteralPath $Root -Filter metatester64.exe -File -Recurse -ErrorAction Stop|Sort-Object FullName|ForEach-Object{$_.FullName})}
 if($items.Count -lt 1){throw 'At least one executable path is required.'}
 [string[]]$normalized=@()
 foreach($item in $items){
  if($null -eq $item -or $item -is [Array] -or $item -isnot [string] -or [string]::IsNullOrWhiteSpace([string]$item)){throw 'invalid executable path collection item'}
  $normalized += [string]$item
 }
 return @($normalized)
}
[string[]]$normalizedExecutablePaths=@(Normalize-NoraExecutablePaths -WasBound $PSBoundParameters.ContainsKey('ExecutablePath') -RawPaths $ExecutablePath -Root $InstallRoot)
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
function ClassificationPath(){Join-Path $EvidenceRoot ('containment-'+$CampaignId+'.classification.json')}
function Assert-NoraExecutablePath([string]$Path){
 if($Path -match '[\x00]' -or $Path -match '^(\\\\|//|\\\\\?\\)' -or $Path -notmatch '^[A-Za-z]:[\\/]' -or $Path -match '(^|[\\/])\.\.([\\/]|$)'){throw 'unsafe containment executable path'}
 if($Path.Length -gt 2 -and $Path.Substring(2).Contains(':')){throw 'alternate data stream in containment executable path'}
 $canonical=[IO.Path]::GetFullPath($Path)
 if(!(Test-Path -LiteralPath $canonical -PathType Leaf)){throw 'missing containment executable'}
 $root=[IO.Path]::GetPathRoot($canonical);if([string]::IsNullOrWhiteSpace($root)){throw 'missing containment executable root'}
 $cursor=Get-Item -LiteralPath $canonical -Force
 if($cursor -isnot [IO.FileInfo]){throw 'containment executable is not a regular file'}
 while($null -ne $cursor){
  $cursorCanonical=[IO.Path]::GetFullPath($cursor.FullName)
  if(![string]::Equals([IO.Path]::GetPathRoot($cursorCanonical),$root,[StringComparison]::OrdinalIgnoreCase)){throw 'containment executable ancestor escapes drive root'}
  if(($cursor.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw 'reparse point containment executable path'}
  if($cursor -is [IO.FileInfo]){$cursor=$cursor.Directory}elseif($cursor -is [IO.DirectoryInfo]){$cursor=$cursor.Parent}else{throw 'unexpected containment executable ancestor type'}
 }
 return $canonical
}
function Bindings(){
 [string[]]$paths=@($normalizedExecutablePaths)
 if($paths.Count -lt 1){throw 'At least one executable path is required.'}
 $seen=@{};$result=@();foreach($path in $paths){$canonical=Assert-NoraExecutablePath $path;if($seen.ContainsKey($canonical.ToLowerInvariant())){throw 'duplicate containment executable'};$seen[$canonical.ToLowerInvariant()]=$true;$result+=[ordered]@{path=$canonical;sha256=Hash $canonical}}
 return @($result|Sort-Object{$_.path.ToUpperInvariant()})
}
function Get-NoraContainmentRules { param([Parameter(Mandatory=$true)][string]$CampaignId) return @(Get-NetFirewallRule -Group (Get-NoraContainmentGroup -RunId $CampaignId) -ErrorAction SilentlyContinue|Sort-Object Name) }
function Get-NoraContainmentRuleViews { param([Parameter(Mandatory=$true)][AllowEmptyCollection()][object[]]$RuleObjects) return @($RuleObjects|ForEach-Object{$rule=$_;[object[]]$apps=@(Get-NetFirewallApplicationFilter -AssociatedNetFirewallRule $rule -ErrorAction Stop);if($apps.Count-ne1){throw 'ambiguous firewall application filter'};[ordered]@{name=$rule.Name;instance_id=[string]$rule.InstanceID;display_name=$rule.DisplayName;group=$rule.Group;enabled=[string]$rule.Enabled;direction=[string]$rule.Direction;action=[string]$rule.Action;profile=[string]$rule.Profile;program=$apps[0].Program}}|Sort-Object program,name,instance_id) }
function AllRuleIdentity(){ $v=@(Get-NetFirewallRule -ErrorAction Stop|Where-Object{[string]$_.Group -ne $firewallGroup}|Sort-Object Name|ForEach-Object{[ordered]@{name=$_.Name;enabled=[string]$_.Enabled;direction=[string]$_.Direction;action=[string]$_.Action;profile=[string]$_.Profile;group=$_.Group}});$b=[Text.Encoding]::UTF8.GetBytes(($v|ConvertTo-Json -Depth 10 -Compress));([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash($b))).Replace('-','').ToLowerInvariant() }
function AssertNoContradictoryAllow($bindings){$allows=@(Get-NetFirewallRule -Direction Outbound -Enabled True -Action Allow -ErrorAction Stop|ForEach-Object{$r=$_;Get-NetFirewallApplicationFilter -AssociatedNetFirewallRule $r -ErrorAction SilentlyContinue|ForEach-Object{[string]$_.Program}});foreach($binding in $bindings){if($allows -contains $binding.path){throw 'contradictory MT5 outbound allow rule'}}}
function State([object[]]$bindings){[object[]]$ruleObjects=@(Get-NoraContainmentRules -CampaignId $CampaignId);[object[]]$ruleViews=@(Get-NoraContainmentRuleViews -RuleObjects $ruleObjects);$connections=@();foreach($process in @(Get-Process terminal64,metatester64 -ErrorAction SilentlyContinue)){$connections+=@(Get-NetTCPConnection -OwningProcess $process.Id -ErrorAction SilentlyContinue|Where-Object{$_.RemoteAddress-notin@('127.0.0.1','::1','0.0.0.0','::')}|ForEach-Object{[ordered]@{pid=$process.Id;process=$process.ProcessName;remote_address=$_.RemoteAddress;remote_port=$_.RemotePort;state=[string]$_.State}})};[ordered]@{schema_version=$schema;campaign_identity=$CampaignId;group=$firewallGroup;captured_utc=(Get-Date).ToUniversalTime().ToString('o');creator=Identity;executables=@($bindings);rules=@($ruleViews);active_rule_count=$ruleObjects.Count;observed_mt5_connections=@($connections);unrelated_firewall_population_identity=AllRuleIdentity}}
function VerifyState($state){
 if($state.schema_version-ne$schema -or $state.campaign_identity-ne$CampaignId -or $state.group-ne$firewallGroup){throw 'containment record identity mismatch'}
 [object[]]$bindings=@(Bindings);[object[]]$recordExecutables=@($state.executables);[object[]]$recordRules=@($state.rules);[object[]]$actualRules=@(Get-NoraContainmentRules -CampaignId $CampaignId);[object[]]$actualViews=@(Get-NoraContainmentRuleViews -RuleObjects $actualRules);if($recordExecutables.Count-ne$bindings.Count -or $recordRules.Count-ne$bindings.Count -or $actualViews.Count-ne$bindings.Count){throw 'containment cardinality mismatch'}
 AssertNoContradictoryAllow $bindings
 for($i=0;$i-lt$bindings.Count;$i++){ $binding=$bindings[$i];[object[]]$rule=@($recordRules|Where-Object{$_.name-eq(RuleName ($i+1))});[object[]]$actual=@($actualViews|Where-Object{$_.name-eq(RuleName ($i+1))});if($rule.Count-ne1 -or $actual.Count-ne1){throw 'missing or duplicate rule GUID binding'};if($rule[0].instance_id-ne$actual[0].instance_id){throw 'rule GUID mismatch'};if($rule[0].program-ne$binding.path -or $recordExecutables[$i].path-ne$binding.path -or $recordExecutables[$i].sha256-ne$binding.sha256){throw 'rule application path or hash mismatch'};if($rule[0].enabled-ne'True' -or $rule[0].direction-ne'Outbound' -or $rule[0].action-ne'Block' -or $rule[0].profile-ne'Any'){throw 'containment rule not active'} }
 return $true
}
function Failure([string]$Reason,[string]$Message){[object[]]$bindings=@();try{$bindings=@(Bindings)}catch{};[object[]]$ruleObjects=@(Get-NoraContainmentRules -CampaignId $CampaignId);[object[]]$ruleViews=@(Get-NoraContainmentRuleViews -RuleObjects $ruleObjects);$classification=if($ruleObjects.Count-eq0){'NO_RULES_TRANSACTION_FAILED'}else{'RULES_PRESENT_RECORD_INCOMPLETE'};$v=[ordered]@{schema_version=$schema;campaign_identity=$CampaignId;classification=$classification;accepted=$false;reason=$Reason;message=$Message;intent_path=IntentPath;final_record_path=FinalPath;active_rule_count=$ruleObjects.Count;executables=@($bindings);rules=@($ruleViews);captured_utc=(Get-Date).ToUniversalTime().ToString('o');creator=Identity};AtomicJson (FailurePath) $v;return $v}
function FreshVerify(){ $verifier=Join-Path $PSScriptRoot 'phase2-network-containment-fresh-verify.ps1';if(!(Test-Path -LiteralPath $verifier -PathType Leaf)){throw 'missing fresh containment verifier'};$args=@('-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',$verifier,'-FinalRecordPath',(FinalPath),'-ExpectedFinalRecordSha256',(Hash (FinalPath)),'-EvidenceRoot',$EvidenceRoot);$output=@(& powershell.exe @args 2>&1);if($LASTEXITCODE-ne0){throw ('fresh record validation failed: '+($output -join "`n"))};return ($output -join "`n")}
function ReadAndValidateFinalRecordForRecovery {
 [byte[]]$bytes=[IO.File]::ReadAllBytes((FinalPath))
 $finalSha=([BitConverter]::ToString(([Security.Cryptography.SHA256]::Create().ComputeHash($bytes)))).Replace('-','').ToLowerInvariant()
 $state=([Text.Encoding]::UTF8.GetString($bytes)).TrimStart([char]0xFEFF)|ConvertFrom-Json
 VerifyState $state|Out-Null
 $acceptedPresent=Test-Path -LiteralPath (AcceptedPath)
 if($acceptedPresent){$accepted=Get-Content -LiteralPath (AcceptedPath) -Raw|ConvertFrom-Json;if($accepted.final_record_sha256-ne$finalSha){throw 'accepted final-record hash mismatch'}}
 return [ordered]@{state=$state;final_record_sha256=$finalSha;accepted_record_present=$acceptedPresent}
}
try {
 switch($Action){
  'stage' {
   [object[]]$bindings=@(Bindings);[object[]]$existingRules=@(Get-NoraContainmentRules -CampaignId $CampaignId);$intent=[ordered]@{schema_version=$schema;phase='intent_prepared';campaign_identity=$CampaignId;repository_commit=$env:NORA_REPOSITORY_COMMIT;creator=Identity;executables=@($bindings);rules=@($existingRules);group=$firewallGroup;intended_rule_names=@(for($i=1;$i-le$bindings.Count;$i++){RuleName $i});intended_final_record_path=FinalPath;evidence_root=$EvidenceRoot;captured_utc=(Get-Date).ToUniversalTime().ToString('o')}
   if(Test-Path -LiteralPath (AcceptedPath)){throw 'accepted containment identity cannot be restaged'}
   if(Test-Path -LiteralPath (ClassificationPath)){throw 'terminal containment classification forbids restaging'}
   if($existingRules.Count -ne 0 -or (Test-Path -LiteralPath (IntentPath))){throw 'stale or incomplete containment transaction requires recovery'}
   AtomicJson (IntentPath) $intent
   $pre=[ordered]@{phase='pre_state_captured';unrelated_firewall_population_identity=AllRuleIdentity;captured_utc=(Get-Date).ToUniversalTime().ToString('o')}
   if($Fault-eq'before_rules'){throw 'forced failure before rules'}
   AssertNoContradictoryAllow $bindings;$i=0;foreach($binding in $bindings){$i++;New-NetFirewallRule -Name (RuleName $i) -DisplayName (RuleName $i) -Group $firewallGroup -Direction Outbound -Action Block -Program $binding.path -RemoteAddress Any -Profile Any -Enabled True -ErrorAction Stop|Out-Null;if($Fault-eq'after_first_rule' -and $i-eq1){throw 'forced failure after first rule'}}
   $state=State $bindings;$state.phase='rules_verified';$state.rules_created_utc=(Get-Date).ToUniversalTime().ToString('o');$state.pre_state=$pre;VerifyState $state|Out-Null
   if($Fault-eq'after_all_rules_before_final'){throw 'forced failure after all rules before final publication'}
   $state.phase='final_record_published';AtomicJson (FinalPath) $state
   if($Fault-eq'after_final_before_accept'){throw 'forced failure after final publication'}
   FreshVerify|Out-Null
   $accepted=[ordered]@{schema_version=$schema;phase='transaction_accepted';verification_phase='final_record_reopened';campaign_identity=$CampaignId;executables=@($state.executables);rules=@($state.rules);intent_sha256=Hash (IntentPath);final_record_path=FinalPath;final_record_sha256=Hash (FinalPath);accepted_utc=(Get-Date).ToUniversalTime().ToString('o');creator=Identity};AtomicJson (AcceptedPath) $accepted
   $accepted|ConvertTo-Json -Depth 20 -Compress
  }
  'verify-final' {if(!(Test-Path -LiteralPath (FinalPath))){throw 'missing final containment record'};$state=Get-Content -LiteralPath (FinalPath) -Raw|ConvertFrom-Json;VerifyState $state|Out-Null;$state|ConvertTo-Json -Depth 20 -Compress}
  'verify' {if(!(Test-Path -LiteralPath (FinalPath)) -or !(Test-Path -LiteralPath (AcceptedPath))){throw 'missing accepted containment records'};$state=Get-Content -LiteralPath (FinalPath) -Raw|ConvertFrom-Json;VerifyState $state|Out-Null;$accepted=Get-Content -LiteralPath (AcceptedPath) -Raw|ConvertFrom-Json;[object[]]$acceptedExecutables=@($accepted.executables);[object[]]$acceptedRules=@($accepted.rules);[object[]]$stateExecutables=@($state.executables);[object[]]$stateRules=@($state.rules);if($accepted.phase-ne'transaction_accepted' -or $accepted.final_record_sha256-ne(Hash (FinalPath)) -or $acceptedExecutables.Count-ne$stateExecutables.Count -or $acceptedRules.Count-ne$stateRules.Count){throw 'accepted transaction binding mismatch'};$state|ConvertTo-Json -Depth 20 -Compress}
  'status' {& $PSCommandPath -Action verify -CampaignId $CampaignId -EvidenceRoot $EvidenceRoot -InstallRoot $InstallRoot -ExecutablePath $normalizedExecutablePaths}
  'smoke' {[object[]]$bindings=@(Bindings);[object[]]$actualRules=@(Get-NoraContainmentRules -CampaignId $CampaignId);[object[]]$syntheticZero=@();[object[]]$syntheticOne=@([pscustomobject]@{name='one'});[object[]]$syntheticTwo=@([pscustomobject]@{name='one'},[pscustomobject]@{name='two'});$intent=[ordered]@{schema_version=$schema;phase='intent_prepared';campaign_identity=$CampaignId;executables=@($bindings);rules=@($syntheticZero);group=$firewallGroup;intended_rule_names=@(for($i=1;$i-le$bindings.Count;$i++){RuleName $i});intended_final_record_path=FinalPath;evidence_root=$EvidenceRoot};$intentJson=$intent|ConvertTo-Json -Depth 20 -Compress;$roundTrip=$intentJson|ConvertFrom-Json;[object[]]$roundTripExecutables=@($roundTrip.executables);[object[]]$roundTripRules=@($roundTrip.rules);if($roundTripExecutables.Count-ne$bindings.Count -or $roundTripRules.Count-ne0){throw 'smoke intent serialization shape'};$v=[ordered]@{schema_version='nora.phase2_containment_runtime_smoke_v3';campaign_identity=$CampaignId;mutation_cmdlets_invoked=$false;normalized_executable_count=$bindings.Count;actual_rule_query_count=$actualRules.Count;executables=@($bindings);expected_rule_names=@($intent.intended_rule_names);intent_round_trip=$true;final_record_serialization=([bool](($intent|ConvertTo-Json -Depth 20 -Compress)|ConvertFrom-Json));cleanup_plan=@($bindings|ForEach-Object{[ordered]@{rule_name=(RuleName ([array]::IndexOf($bindings,$_)+1));program=$_.path}});synthetic_firewall_result_counts=[ordered]@{zero=$syntheticZero.Count;one=$syntheticOne.Count;multiple=$syntheticTwo.Count};synthetic_application_filter_counts=[ordered]@{zero=$syntheticZero.Count;one=$syntheticOne.Count;multiple=$syntheticTwo.Count};synthetic_guid_counts=[ordered]@{zero=$syntheticZero.Count;one=$syntheticOne.Count;multiple=$syntheticTwo.Count};synthetic_rule_json_shapes=[ordered]@{zero=@($syntheticZero);one=@($syntheticOne);multiple=@($syntheticTwo)}};$v|ConvertTo-Json -Depth 20 -Compress}
  'recover' {[object[]]$rules=@(Get-NoraContainmentRules -CampaignId $CampaignId);$intentPresent=Test-Path -LiteralPath (IntentPath);$finalPresent=Test-Path -LiteralPath (FinalPath);$acceptedPresent=Test-Path -LiteralPath (AcceptedPath);$finalSha=$null;$finalValid=$false;if($finalPresent){$validated=ReadAndValidateFinalRecordForRecovery;$finalSha=$validated.final_record_sha256;$finalValid=$true};$classification=if($rules.Count-eq0 -and !$intentPresent){'NO_RULES_NO_RECORD'}elseif($rules.Count-eq0){'NO_RULES_TRANSACTION_FAILED'}elseif(!$finalPresent){'RULES_PRESENT_RECORD_INCOMPLETE'}else{'RECORD_PRESENT_REQUIRES_VERIFY'};$v=[ordered]@{schema_version=$schema;campaign_identity=$CampaignId;classification=$classification;active_rule_count=$rules.Count;rules=@($rules);intent_present=$intentPresent;final_record_present=$finalPresent;final_record_sha256=$finalSha;final_record_valid=$finalValid;accepted_record_present=$acceptedPresent;recovered_utc=(Get-Date).ToUniversalTime().ToString('o')};AtomicJson (RecoveryPath) $v;$v|ConvertTo-Json -Depth 20 -Compress}
  'cleanup' {[object[]]$bindings=@(Bindings);$before=State $bindings;[object[]]$rules=@(Get-NoraContainmentRules -CampaignId $CampaignId);foreach($rule in $rules){Remove-NetFirewallRule -Name $rule.Name -ErrorAction Stop};[object[]]$remaining=@(Get-NoraContainmentRules -CampaignId $CampaignId);if($remaining.Count-ne0){throw 'containment cleanup incomplete'};$after=AllRuleIdentity;$v=[ordered]@{schema_version=$schema;campaign_identity=$CampaignId;cleanup='pass';removed_rule_count=$rules.Count;removed_rules=@($rules|ForEach-Object{[ordered]@{name=$_.Name;instance_id=[string]$_.InstanceID}});remaining_rules=@($remaining);unrelated_rules_before_sha256=$before.unrelated_firewall_population_identity;unrelated_rules_after_sha256=$after;unrelated_rules_unchanged=($before.unrelated_firewall_population_identity-eq$after);completed_utc=(Get-Date).ToUniversalTime().ToString('o')};if(!$v.unrelated_rules_unchanged){throw 'unrelated firewall rules changed during cleanup'};AtomicJson (Join-Path $EvidenceRoot ('containment-'+$CampaignId+'-cleanup.json')) $v;$v|ConvertTo-Json -Depth 20 -Compress}
 }
} catch {Failure $_.Exception.GetType().FullName $_.Exception.Message|Out-Null;[Console]::Error.WriteLine($_.Exception.Message);exit 1}
