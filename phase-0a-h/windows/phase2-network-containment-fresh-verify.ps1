[CmdletBinding()]
param(
 [Parameter(Mandatory=$true)][string]$FinalRecordPath,
 [Parameter(Mandatory=$true)][ValidatePattern('^[0-9a-fA-F]{64}$')][string]$ExpectedFinalRecordSha256,
 [Parameter(Mandatory=$true)][string]$EvidenceRoot
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$schema='nora.phase2_mt5_network_containment_transaction_v3'
function HashBytes([byte[]]$Bytes){([BitConverter]::ToString(([Security.Cryptography.SHA256]::Create()).ComputeHash($Bytes))).Replace('-','').ToLowerInvariant()}
function FullPath([string]$Path){if([string]::IsNullOrWhiteSpace($Path) -or $Path.IndexOf([char]0) -ge 0){throw 'invalid final record path'};if($Path -match '^(\\\\|//|\\\\\?\\)' -or $Path -notmatch '^[A-Za-z]:[\\/]'){throw 'unsupported final record path'};if($Path -match '(^|[\\/])\.\.([\\/]|$)' -or ($Path.Length -gt 2 -and $Path.Substring(2).Contains(':'))){throw 'unsafe final record path'};[IO.Path]::GetFullPath($Path)}
function AssertUnderRoot([string]$Root,[string]$Child){$r=[IO.Path]::GetFullPath($Root).TrimEnd([IO.Path]::DirectorySeparatorChar,[IO.Path]::AltDirectorySeparatorChar);$c=[IO.Path]::GetFullPath($Child);if(![string]::Equals([IO.Path]::GetPathRoot($r),[IO.Path]::GetPathRoot($c),[StringComparison]::OrdinalIgnoreCase)){throw 'final record drive mismatch'};$prefix=$r+[IO.Path]::DirectorySeparatorChar;if(![string]::Equals($r,$c,[StringComparison]::OrdinalIgnoreCase) -and !$c.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)){throw 'final record outside evidence root'};$cursor=Get-Item -LiteralPath $c -Force -ErrorAction Stop;while($null -ne $cursor){if(($cursor.Attributes-band[IO.FileAttributes]::ReparsePoint)-ne0){throw 'final record reparse point'};if($cursor -is [IO.FileInfo]){$cursor=$cursor.Directory}elseif($cursor -is [IO.DirectoryInfo]){$cursor=$cursor.Parent}else{throw 'unexpected final record object type'}};return $c}
function Get-NoraRules([string]$Group){[object[]]$rules=@(Get-NetFirewallRule -Group $Group -ErrorAction Stop|Sort-Object Name);return @($rules)}
function Get-NoraViews([AllowEmptyCollection()][object[]]$Rules){return @($Rules|ForEach-Object{$rule=$_;[object[]]$apps=@(Get-NetFirewallApplicationFilter -AssociatedNetFirewallRule $rule -ErrorAction Stop);if($apps.Count-ne1){throw 'firewall application filter cardinality mismatch'};[ordered]@{name=$rule.Name;instance_id=[string]$rule.InstanceID;group=[string]$rule.Group;enabled=[string]$rule.Enabled;direction=[string]$rule.Direction;action=[string]$rule.Action;profile=[string]$rule.Profile;program=[string]$apps[0].Program}}|Sort-Object program,name,instance_id)}
try {
 $recordPath=AssertUnderRoot $EvidenceRoot (FullPath $FinalRecordPath)
 if(!(Test-Path -LiteralPath $recordPath -PathType Leaf)){throw 'missing final record'}
 [byte[]]$bytes=[IO.File]::ReadAllBytes($recordPath);$actualHash=HashBytes $bytes;if($actualHash -ne $ExpectedFinalRecordSha256.ToLowerInvariant()){throw 'final record hash mismatch'}
 $record=([Text.Encoding]::UTF8.GetString($bytes)|ConvertFrom-Json)
 if($record.schema_version-ne$schema -or [string]::IsNullOrWhiteSpace([string]$record.campaign_identity)){throw 'final record schema or campaign identity mismatch'}
 $campaign=[string]$record.campaign_identity;if($campaign -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$'){throw 'invalid campaign identity'};$group='NoraPhase2Containment-'+$campaign
 [object[]]$executables=@($record.executables);[object[]]$expectedRules=@($record.rules);if($executables.Count -lt 1 -or $expectedRules.Count -ne$executables.Count){throw 'final record collection cardinality mismatch'}
 [object[]]$actualRules=@(Get-NoraRules $group);[object[]]$actualViews=@(Get-NoraViews $actualRules);if($actualViews.Count-ne$expectedRules.Count){throw 'actual rule cardinality mismatch'}
 for($i=0;$i-lt$executables.Count;$i++){ $e=$executables[$i];if($e.path -isnot [string] -or [string]::IsNullOrWhiteSpace($e.path) -or $e.sha256 -notmatch '^[0-9a-f]{64}$'){throw 'invalid executable binding'};if((Get-FileHash -Algorithm SHA256 -LiteralPath $e.path -ErrorAction Stop).Hash.ToLowerInvariant() -ne $e.sha256){throw 'executable hash mismatch'};$name='NoraPhase2Containment-'+$campaign+'-'+($i+1);[object[]]$expected=@($expectedRules|Where-Object{$_.name-eq$name});[object[]]$actual=@($actualViews|Where-Object{$_.name-eq$name});if($expected.Count-ne1 -or $actual.Count-ne1){throw 'rule name or GUID mismatch'};if($expected[0].instance_id-ne$actual[0].instance_id -or $actual[0].program-ne$e.path -or $actual[0].group-ne$group -or $actual[0].enabled-ne'True' -or $actual[0].direction-ne'Outbound' -or $actual[0].action-ne'Block' -or $actual[0].profile-ne'Any'){throw 'actual rule binding mismatch'}}
 [ordered]@{schema_version='nora.phase2_mt5_network_containment_fresh_verification_v1';campaign_identity=$campaign;final_record_path=$recordPath;final_record_sha256=$actualHash;executable_count=$executables.Count;rule_count=$actualViews.Count;rules=@($actualViews);verified_utc=(Get-Date).ToUniversalTime().ToString('o')}|ConvertTo-Json -Depth 20 -Compress
} catch { [Console]::Error.WriteLine($_.Exception.Message);exit 1 }
