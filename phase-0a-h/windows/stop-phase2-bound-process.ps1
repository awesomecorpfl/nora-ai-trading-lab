[CmdletBinding()]
param(
 [Parameter(Mandatory=$true)][int]$ProcessId,
 [Parameter(Mandatory=$true)][string]$ExpectedStartTimeUtc,
 [Parameter(Mandatory=$true)][string]$ExpectedCommandLineSha256,
 [Parameter(Mandatory=$true)][string]$ExpectedOwner
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
function HashText([string]$value){$bytes=[Text.Encoding]::UTF8.GetBytes($value);([Security.Cryptography.SHA256]::Create().ComputeHash($bytes)|ForEach-Object{$_.ToString('x2')})-join''}
if($ProcessId-eq$PID-or$ExpectedCommandLineSha256-notmatch'^[0-9a-f]{64}$'){throw 'invalid bound process identity'}
$cim=Get-CimInstance Win32_Process -Filter ('ProcessId='+$ProcessId) -ErrorAction Stop
if(!$cim){throw 'bound process missing'}
$ownerResult=Invoke-CimMethod -InputObject $cim -MethodName GetOwner -ErrorAction Stop
$owner=$ownerResult.Domain+'\'+$ownerResult.User
$process=Get-Process -Id $ProcessId -ErrorAction Stop
$start=$process.StartTime.ToUniversalTime().ToString('o')
$commandHash=HashText ([string]$cim.CommandLine)
if($start-ne$ExpectedStartTimeUtc-or$commandHash-ne$ExpectedCommandLineSha256-or!([string]::Equals($owner,$ExpectedOwner,[StringComparison]::OrdinalIgnoreCase))){throw 'bound process identity mismatch'}
Stop-Process -Id $ProcessId -Force -ErrorAction Stop
$process.WaitForExit(10000)|Out-Null
if(Get-Process -Id $ProcessId -ErrorAction SilentlyContinue){throw 'bound process did not terminate'}
[ordered]@{process_id=$ProcessId;start_time_utc=$start;command_line_sha256=$commandHash;owner=$owner;terminated=$true}|ConvertTo-Json -Compress
