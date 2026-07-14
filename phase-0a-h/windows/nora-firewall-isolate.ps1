<#
.SYNOPSIS
  Bounded, reversible, executable-scoped outbound network isolation for the
  Nora embedded-fixture MT5 tester canary.

.DESCRIPTION
  Creates two Windows Defender Firewall outbound-block rules scoped exactly to
  the MT5 terminal and tester-agent executables, identified by a unique RunId.
  Loopback (127.0.0.1, used by the terminal to reach the local agent on port
  3000) is not filtered by Windows Firewall, so the local agent channel stays
  open while remote trade/history-server access is blocked. SSH management
  (sshd.exe) is a separate process and is never affected.

  -Action enable:  remove any stale rules for RunId (safety), create the two
                   rules, then verify exactly two exist. Fails closed on error.
  -Action disable: remove the two rules for RunId and verify zero remain.
  -Action status:  report how many rules exist for RunId.

  Cleanup is idempotent: calling disable twice or after an interruption is safe.
#>
param(
  [Parameter(Mandatory=$true)][string]$RunId,
  [ValidateSet('enable','disable','status')][string]$Action='status',
  [string]$Terminal='C:\Program Files\Darwinex MetaTrader 5\terminal64.exe',
  [string]$Agent='C:\Program Files\Darwinex MetaTrader 5\metatester64.exe'
)
$ErrorActionPreference='Stop'
if($RunId -notmatch '^[A-Za-z0-9_.-]+$'){throw 'invalid RunId'}
$prefix="nora-$RunId"
function CountRules(){@(Get-NetFirewallRule -DisplayName "$prefix*" -ErrorAction SilentlyContinue).Count}
function RemoveRules(){Get-NetFirewallRule -DisplayName "$prefix*" -ErrorAction SilentlyContinue | Remove-NetFirewallRule -ErrorAction SilentlyContinue}
switch($Action){
 'enable'{
  RemoveRules
  if(-not(Test-Path $Terminal)){throw "terminal exe missing: $Terminal"}
  if(-not(Test-Path $Agent)){throw "agent exe missing: $Agent"}
  New-NetFirewallRule -DisplayName "$prefix-terminal" -Direction Outbound -Action Block -Program $Terminal -Enabled True -Profile Any -Group "Nora-Isolate-$RunId" | Out-Null
  New-NetFirewallRule -DisplayName "$prefix-agent" -Direction Outbound -Action Block -Program $Agent -Enabled True -Profile Any -Group "Nora-Isolate-$RunId" | Out-Null
  $c=CountRules
  if($c -ne 2){RemoveRules; throw "expected 2 isolation rules, got $c"}
  Write-Output "ISOLATE_ENABLE_OK rules=$c run=$RunId"
 }
 'disable'{
  RemoveRules
  $c=CountRules
  if($c -ne 0){throw "cleanup failed, $c rules remain for $RunId"}
  Write-Output "ISOLATE_DISABLE_OK rules=$c run=$RunId"
 }
 'status'{
  $c=CountRules
  Write-Output "ISOLATE_STATUS rules=$c run=$RunId"
 }
}
