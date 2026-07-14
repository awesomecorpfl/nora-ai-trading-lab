param(
 [Parameter(Mandatory=$true)][string]$Template,
 [Parameter(Mandatory=$true)][string]$Destination,
 [Parameter(Mandatory=$true)][ValidateSet('GDAXI','AUDCAD')][string]$Symbol,
 [Parameter(Mandatory=$true)][string]$Report
)
$ErrorActionPreference='Stop'
function ReplaceLine([string]$Text,[string]$Key,[string]$Value){
 $pattern='(?m)^'+[regex]::Escape($Key)+'=.*$'
 if($Text -notmatch $pattern){throw "missing template key $Key"}
 [regex]::Replace($Text,$pattern,$Key+'='+$Value)
}
if(!(Test-Path -LiteralPath $Template -PathType Leaf)){throw 'missing tester template'}
$ini=Get-Content -LiteralPath $Template -Raw
foreach($key in @('Environment','Login','Server')){if($ini -notmatch ('(?m)^'+$key+'=.+$')){throw "template lacks configured $key"}}
$values=[ordered]@{Expert='NoraPhase2TenStrategy\NoraPhase2TenStrategyTesterCanaryV1';Symbol=$Symbol;Period='M1';Model='0';FromDate='2020.07.01';ToDate='2026.07.01';Report=$Report;ReplaceReport='1';ShutdownTerminal='1';UseLocal='1';UseRemote='0';UseCloud='0';Visual='0'}
foreach($entry in $values.GetEnumerator()){$ini=ReplaceLine $ini $entry.Key $entry.Value}
Set-Content -LiteralPath $Destination -Value $ini -Encoding ascii
