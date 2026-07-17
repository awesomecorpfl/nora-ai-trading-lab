[CmdletBinding()]
param(
 [Parameter(Mandatory=$true)][ValidateSet('run','reserve','capture','complete','status','recover','smoke')][string]$Mode,
 [Parameter(Mandatory=$true)][string]$CampaignId,
 [Parameter(Mandatory=$true)][string]$RepositoryCommit,
 [Parameter(Mandatory=$true)][string]$CaptureToolPath,
 [Parameter(Mandatory=$true)][string]$CaptureToolSha256,
 [Parameter(Mandatory=$true)][string]$RunnerPath,
 [Parameter(Mandatory=$true)][string]$RunnerSha256,
 [Parameter(Mandatory=$true)][string]$WrapperPath,
 [Parameter(Mandatory=$true)][string]$WrapperSha256,
 [string]$LogicalCommandSha256,[string]$SubmittedCommandSha256,[int]$WrapperPid=0,[string]$WrapperStartUtc,
 [string]$LaunchId,
 [string]$EvidenceRoot='C:\NoraEvidence\Phase2',
 [ValidateRange(1,100)][int]$CaptureCount=20,
 [ValidateRange(0,3600)][int]$CaptureIntervalSeconds=0,
 [ValidateRange(1,100)][int]$Slot=0,
 [string]$OwnerToken
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$schema='nora.phase2_firewall_campaign_v1'

function Hash([string]$Path){(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()}
function AtomicJson([string]$Path,$Value){$tmp=$Path+'.partial.'+[guid]::NewGuid().ToString('N');[IO.File]::WriteAllText($tmp,($Value|ConvertTo-Json -Depth 30 -Compress),[Text.UTF8Encoding]::new($false));$s=[IO.File]::Open($tmp,'Open','ReadWrite','None');$s.Flush($true);$s.Dispose();if(Test-Path -LiteralPath $Path){throw 'immutable publication target already exists'};[IO.File]::Move($tmp,$Path)}
function UTC(){(Get-Date).ToUniversalTime().ToString('o')}
function RequireId(){if($CampaignId-notmatch'^[A-Za-z0-9][A-Za-z0-9._-]{7,127}$'){throw 'invalid campaign id'};if($RepositoryCommit-notmatch'^[0-9a-f]{40}$'){throw 'invalid repository commit'};if($LaunchId -and $LaunchId-notmatch'^[A-Za-z0-9][A-Za-z0-9._-]{7,127}$'){throw 'invalid launch id'};if($SubmittedCommandSha256-notmatch'^[0-9a-f]{64}$' -or $SubmittedCommandSha256 -eq 'unavailable'){throw 'submitted command identity unavailable'};if($LogicalCommandSha256-notmatch'^[0-9a-f]{64}$' -or $LogicalCommandSha256 -eq 'unavailable'){throw 'logical command identity unavailable'};if(!(Test-Path -LiteralPath $CaptureToolPath -PathType Leaf) -or (Hash $CaptureToolPath)-ne$CaptureToolSha256.ToLowerInvariant()){throw 'capture tool identity mismatch'};if(!(Test-Path -LiteralPath $RunnerPath -PathType Leaf) -or (Hash $RunnerPath)-ne$RunnerSha256.ToLowerInvariant()){throw 'runner identity mismatch'}}
function Root(){Join-Path (Join-Path $EvidenceRoot 'firewall-campaigns') $CampaignId}
function OwnerPath(){Join-Path (Root) 'owner.json'}
function CompletionPath(){Join-Path (Root) 'completion.json'}
function SlotName([int]$Number){$Number.ToString('00')}
function ClaimPath([int]$Number){Join-Path (Join-Path (Root) 'claims') ((SlotName $Number)+'.json')}
function ReceiptPath([int]$Number){Join-Path (Join-Path (Root) 'receipts') ((SlotName $Number)+'.json')}
function FinalPath([int]$Number){Join-Path (Join-Path (Root) 'captures') ((SlotName $Number)+'.json')}
function Owner(){if(!(Test-Path -LiteralPath (OwnerPath) -PathType Leaf)){throw 'missing immutable campaign owner'};Get-Content -LiteralPath (OwnerPath) -Raw|ConvertFrom-Json}
function ProcessStart(){try{([datetime](Get-CimInstance Win32_Process -Filter ('ProcessId='+$PID)).CreationDate).ToUniversalTime().ToString('o')}catch{$null}}
function CommandHash(){$v=[ordered]@{path=$PSCommandPath;mode=$Mode;campaign_id=$CampaignId;repository_commit=$RepositoryCommit;runner_sha256=$RunnerSha256;capture_tool_sha256=$CaptureToolSha256;capture_count=$CaptureCount;capture_interval_seconds=$CaptureIntervalSeconds};$b=[Text.Encoding]::UTF8.GetBytes(($v|ConvertTo-Json -Compress));([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash($b))).Replace('-','').ToLowerInvariant()}
function Reserve(){
 RequireId;$base=Join-Path $EvidenceRoot 'firewall-campaigns';New-Item -ItemType Directory -Path $base -Force|Out-Null
 # New-Item without Force is the atomic campaign-identity claim.  A partially created root is intentionally terminal.
 New-Item -ItemType Directory -Path (Root) -ErrorAction Stop|Out-Null
 foreach($d in 'claims','captures','receipts','temporary','partials'){New-Item -ItemType Directory -Path (Join-Path (Root) $d) -ErrorAction Stop|Out-Null}
 $token=if($OwnerToken){$OwnerToken}else{[guid]::NewGuid().ToString('N')+[guid]::NewGuid().ToString('N')}
 $o=[ordered]@{schema_version=$schema;campaign_id=$CampaignId;launch_id=$LaunchId;host_identity=[Security.Principal.WindowsIdentity]::GetCurrent().Name;windows_user=[Security.Principal.WindowsIdentity]::GetCurrent().Name;owner_pid=$PID;owner_process_start_utc=ProcessStart;parent_process_id=(Get-CimInstance Win32_Process -Filter ('ProcessId='+$PID)).ParentProcessId;launcher_path=$PSCommandPath;normalized_command_sha256=CommandHash;repository_commit=$RepositoryCommit;runner_path=$RunnerPath;runner_sha256=$RunnerSha256;capture_tool_path=$CaptureToolPath;capture_tool_sha256=$CaptureToolSha256;expected_capture_count=$CaptureCount;capture_interval_seconds=$CaptureIntervalSeconds;created_utc=UTC;owner_token_sha256=([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($token)))).Replace('-','').ToLowerInvariant();state='reserved'}
 $cp=Get-CimInstance Win32_Process -Filter ('ProcessId='+$PID);$user=[Security.Principal.WindowsIdentity]::GetCurrent();$o.wrapper_path=$WrapperPath;$o.wrapper_sha256=$WrapperSha256;$o.logical_command_sha256=$LogicalCommandSha256;$o.submitted_command_sha256=$SubmittedCommandSha256;$o.wrapper_pid=$WrapperPid;$o.wrapper_start_utc=$WrapperStartUtc;$o.user_sid=$user.User.Value;$o.campaign_process=[ordered]@{pid=$PID;creation_time_utc=ProcessStart;executable_path=[string]$cp.ExecutablePath;command_line=[string]$cp.CommandLine;windows_user=$user.Name;user_sid=$user.User.Value};$o.campaign_executable_path=$cp.ExecutablePath;$o.campaign_command_line=$cp.CommandLine
 AtomicJson (OwnerPath) $o;[ordered]@{campaign_root=Root;owner_path=OwnerPath;owner_sha256=Hash (OwnerPath);owner_token=$token}|ConvertTo-Json -Compress
}
function Claim([int]$Number,[string]$Token){if($Number-lt1-or$Number-gt$CaptureCount){throw 'slot outside campaign range'};$o=Owner;if((HashToken $Token)-ne$o.owner_token_sha256){throw 'foreign campaign owner'};if(Test-Path -LiteralPath (FinalPath $Number)){throw 'final capture already exists'};if(Test-Path -LiteralPath (ReceiptPath $Number)){throw 'slot receipt already exists'};$claim=[ordered]@{schema_version='nora.phase2_firewall_campaign_slot_claim_v1';campaign_id=$CampaignId;slot=$Number;owner_sha256=Hash (OwnerPath);owner_pid=$PID;owner_process_start_utc=ProcessStart;claim_utc=UTC;capture_tool_sha256=$CaptureToolSha256;repository_commit=$RepositoryCommit;state='claimed'};AtomicJson (ClaimPath $Number) $claim;return $claim}
function HashToken([string]$Token){if([string]::IsNullOrWhiteSpace($Token)){throw 'missing owner token'};([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($Token)))).Replace('-','').ToLowerInvariant()}
function Capture([int]$Number,[string]$Token){
 RequireId;$claim=Claim $Number $Token;$temporary=Join-Path (Join-Path (Root) 'temporary') ((SlotName $Number)+'.'+[guid]::NewGuid().ToString('N')+'.json');
 try {
  $out=& $CaptureToolPath -Mode capture -DestinationPath $temporary -RepositoryCommit $RepositoryCommit -EvidenceRoot $EvidenceRoot
  $published=ConvertFrom-Json ([string]$out);if(!(Test-Path -LiteralPath $temporary -PathType Leaf) -or $published.sha256-ne(Hash $temporary)){throw 'capture publication identity mismatch'}
  if(Test-Path -LiteralPath (FinalPath $Number)){throw 'final capture overwrite attempt'}
  [IO.File]::Move($temporary,(FinalPath $Number))
  $receipt=[ordered]@{schema_version='nora.phase2_firewall_campaign_slot_receipt_v1';campaign_id=$CampaignId;slot=$Number;claim_path=(ClaimPath $Number);claim_sha256=Hash (ClaimPath $Number);owner_sha256=Hash (OwnerPath);temporary_path=$temporary;temporary_sha256=$published.sha256;final_path=(FinalPath $Number);final_size=(Get-Item -LiteralPath (FinalPath $Number)).Length;final_sha256=Hash (FinalPath $Number);capture_tool_sha256=$CaptureToolSha256;repository_commit=$RepositoryCommit;capture_order=$Number;claimed_utc=$claim.claim_utc;published_utc=UTC;state='published'};AtomicJson (ReceiptPath $Number) $receipt;return $receipt
 } catch {if(Test-Path -LiteralPath $temporary){$partial=Join-Path (Join-Path (Root) 'partials') ((SlotName $Number)+'.'+[guid]::NewGuid().ToString('N')+'.partial.json');Move-Item -LiteralPath $temporary -Destination $partial;AtomicJson ((ClaimPath $Number)+'.partial.json') ([ordered]@{schema_version='nora.phase2_firewall_campaign_partial_v1';campaign_id=$CampaignId;slot=$Number;claim_sha256=Hash (ClaimPath $Number);partial_path=$partial;partial_sha256=Hash $partial;classified_utc=UTC;state='abandoned_partial'})};throw}
}
function Complete([string]$Token){$o=Owner;if((HashToken $Token)-ne$o.owner_token_sha256){throw 'foreign campaign owner'};if(Test-Path -LiteralPath (CompletionPath)){throw 'completed immutable campaign cannot be resumed'};$receipts=@();for($i=1;$i-le$CaptureCount;$i++){if(!(Test-Path -LiteralPath (ClaimPath $i)) -or !(Test-Path -LiteralPath (ReceiptPath $i)) -or !(Test-Path -LiteralPath (FinalPath $i))){throw 'missing campaign slot'};$r=Get-Content -LiteralPath (ReceiptPath $i) -Raw|ConvertFrom-Json;if($r.campaign_id-ne$CampaignId-or[int]$r.slot-ne$i-or$r.owner_sha256-ne(Hash (OwnerPath)) -or $r.capture_tool_sha256-ne$CaptureToolSha256 -or $r.final_sha256-ne(Hash (FinalPath $i))){throw 'slot identity mismatch'};$receipts+=@($r)};if(@(Get-ChildItem -LiteralPath (Join-Path (Root) 'partials') -File).Count-ne0){throw 'unresolved campaign partial'};$paths=@($receipts|ForEach-Object{$_.final_path});if(@($paths|Sort-Object -Unique).Count-ne$CaptureCount){throw 'duplicate final artifact path'};AtomicJson (CompletionPath) ([ordered]@{schema_version=$schema;campaign_id=$CampaignId;owner_sha256=Hash (OwnerPath);repository_commit=$RepositoryCommit;capture_tool_sha256=$CaptureToolSha256;expected_capture_count=$CaptureCount;receipt_paths=@(1..$CaptureCount|ForEach-Object{ReceiptPath $_});receipt_sha256=@(1..$CaptureCount|ForEach-Object{Hash (ReceiptPath $_)});capture_paths=@(1..$CaptureCount|ForEach-Object{FinalPath $_});capture_sha256=@(1..$CaptureCount|ForEach-Object{Hash (FinalPath $_)});completed_utc=UTC;state='complete'})
}
function Status(){[ordered]@{campaign_id=$CampaignId;root=Root;owner_present=(Test-Path -LiteralPath (OwnerPath));completion_present=(Test-Path -LiteralPath (CompletionPath));claim_count=@(Get-ChildItem -LiteralPath (Join-Path (Root) 'claims') -Filter '*.json' -File -ErrorAction SilentlyContinue).Count;receipt_count=@(Get-ChildItem -LiteralPath (Join-Path (Root) 'receipts') -Filter '*.json' -File -ErrorAction SilentlyContinue).Count;final_count=@(Get-ChildItem -LiteralPath (Join-Path (Root) 'captures') -Filter '*.json' -File -ErrorAction SilentlyContinue).Count;partial_count=@(Get-ChildItem -LiteralPath (Join-Path (Root) 'partials') -File -ErrorAction SilentlyContinue).Count}|ConvertTo-Json -Compress}
function Run(){ $reservation=Reserve|ConvertFrom-Json;$token=$reservation.owner_token;for($i=1;$i-le$CaptureCount;$i++){Capture $i $token|Out-Null;if($CaptureIntervalSeconds-gt0 -and $i-lt$CaptureCount){Start-Sleep -Seconds $CaptureIntervalSeconds}};Complete $token;Status }
RequireId
switch($Mode){
 'run' { Run }
 'reserve' { Reserve }
 'capture' { if(!$OwnerToken){throw 'capture requires exact owner token'};Capture $Slot $OwnerToken|ConvertTo-Json -Depth 20 -Compress }
 'complete' { if(!$OwnerToken){throw 'complete requires exact owner token'};Complete $OwnerToken;Status }
 'status' { Status }
 'recover' { throw 'recovery requires separately authorized exact-owner procedure' }
 'smoke' { [ordered]@{schema_version='nora.phase2_firewall_campaign_smoke_v1';mutation_cmdlets_invoked=$false;campaign_id=$CampaignId}|ConvertTo-Json -Compress }
}
