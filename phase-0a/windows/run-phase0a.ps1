[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][ValidatePattern('^[A-Za-z0-9_-]+$')][string]$RunId,
  [Parameter(Mandatory = $true)][string]$IncomingRoot,
  [int]$TimeoutSeconds = 900
)

$ErrorActionPreference = 'Stop'
$workRoot = Join-Path $env:USERPROFILE 'NoraPhase0A'
$runRoot = Join-Path (Join-Path $workRoot 'runs') $RunId
$state = [ordered]@{ run_id = $RunId; started_utc = (Get-Date).ToUniversalTime().ToString('o'); status = 'starting' }

function Write-State {
  $state | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $runRoot 'status.json') -Encoding UTF8
}
function Find-TerminalDataRoot {
  $candidate = Get-ChildItem -Path (Join-Path $env:APPDATA 'MetaQuotes\Terminal') -Directory | Where-Object {
    $origin = Join-Path $_.FullName 'origin.txt'
    (Test-Path $origin) -and ((Get-Content $origin -Raw).Trim() -eq 'C:\Program Files\Darwinex MetaTrader 5')
  } | Select-Object -First 1
  if ($null -eq $candidate) { throw 'Could not discover Darwinex terminal data root from origin.txt.' }
  return $candidate.FullName
}
function Write-Manifest([string]$DataRoot, [string]$OutFile) {
  $historyRoot = Join-Path $DataRoot 'bases\Darwinex-Live\history\GDAXI'
  if (-not (Test-Path $historyRoot)) { throw "Pinned GDAXI history path is absent: $historyRoot" }
  $files = Get-ChildItem -LiteralPath $historyRoot -File -Recurse | Sort-Object FullName
  if ($files.Count -eq 0) { throw "Pinned GDAXI history path has no files: $historyRoot" }
  $manifest = foreach ($file in $files) {
    [pscustomobject]@{ path = $file.FullName.Substring($DataRoot.Length + 1); bytes = $file.Length; sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash }
  }
  $manifest | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath $OutFile -Encoding UTF8
  return (Get-FileHash -LiteralPath $OutFile -Algorithm SHA256).Hash
}
function Get-IniValue([string]$Path, [string]$Key) {
  $line = Get-Content -LiteralPath $Path | Where-Object { $_ -match ("^{0}=" -f [regex]::Escape($Key)) } | Select-Object -First 1
  if ($null -eq $line) { throw "Existing tester configuration lacks $Key." }
  return $line.Substring($Key.Length + 1).Trim()
}

try {
  if (Test-Path $runRoot) { Remove-Item -LiteralPath $runRoot -Recurse -Force }
  New-Item -ItemType Directory -Path $runRoot -Force | Out-Null
  Write-State
  $terminal = 'C:\Program Files\Darwinex MetaTrader 5\terminal64.exe'
  $editor = 'C:\Program Files\Darwinex MetaTrader 5\MetaEditor64.exe'
  if (-not (Test-Path $terminal) -or -not (Test-Path $editor)) { throw 'Expected Darwinex MT5 executables are missing.' }
  $dataRoot = Find-TerminalDataRoot
  $state.data_root = $dataRoot
  $state.terminal_version = (Get-Item $terminal).VersionInfo.FileVersion
  $state.history_manifest_sha256 = Write-Manifest $dataRoot (Join-Path $runRoot 'history-manifest.json')
  $expertDir = Join-Path $dataRoot 'MQL5\Experts\NoraPhase0A'
  New-Item -ItemType Directory -Path $expertDir -Force | Out-Null
  $targetSource = Join-Path $expertDir 'Phase0Probe.mq5'
  Copy-Item -LiteralPath (Join-Path $IncomingRoot 'Phase0Probe.mq5') -Destination $targetSource -Force
  $compileLog = Join-Path $runRoot 'compile.log'
  $compile = Start-Process -FilePath $editor -ArgumentList ('/compile:"{0}" /log:"{1}"' -f $targetSource,$compileLog) -Wait -PassThru
  $expertBinary = [System.IO.Path]::ChangeExtension($targetSource, '.ex5')
  # This installed MetaEditor returns 1 even after a logged successful compile; the
  # generated binary is the authoritative success condition.
  $state.metaeditor_exit_code = $compile.ExitCode
  if (-not (Test-Path $expertBinary)) { throw "EA compilation produced no binary (exit $($compile.ExitCode)); see compile.log." }
  Copy-Item -LiteralPath $expertBinary -Destination (Join-Path $runRoot 'Phase0Probe.ex5') -Force
  $state.ea_sha256 = (Get-FileHash -LiteralPath $expertBinary -Algorithm SHA256).Hash
  $profileDir = Join-Path $dataRoot 'MQL5\Profiles\Tester'
  New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
  $setName = "NoraPhase0A-$RunId.set"
  $setPath = Join-Path $profileDir $setName
  (Get-Content (Join-Path $IncomingRoot 'probe.set.template') -Raw).Replace('__RUN_ID__', $RunId) | Set-Content -LiteralPath $setPath -Encoding ASCII
  $reportPath = Join-Path $runRoot 'report.htm'
  $configPath = Join-Path $runRoot 'tester.ini'
  $existingTesterConfig = 'C:\Program Files\Darwinex MetaTrader 5\backtest_run.ini'
  if (-not (Test-Path $existingTesterConfig)) { throw 'Existing MT5 tester configuration is absent; refusing to choose an account.' }
  $login = Get-IniValue $existingTesterConfig 'Login'
  $server = Get-IniValue $existingTesterConfig 'Server'
  (Get-Content (Join-Path $IncomingRoot 'tester.template.ini') -Raw).Replace('__LOGIN__',$login).Replace('__SERVER__',$server).Replace('__SET_FILE__',$setName).Replace('__REPORT_PATH__',$reportPath) | Set-Content -LiteralPath $configPath -Encoding ASCII
  $state.config_sha256 = (Get-FileHash -LiteralPath $configPath -Algorithm SHA256).Hash
  $state.status = 'running'; Write-State
  $process = Start-Process -FilePath $terminal -ArgumentList ('/config:"{0}"' -f $configPath) -PassThru
  if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
    Stop-Process -Id $process.Id -Force
    throw "MT5 terminal exceeded $TimeoutSeconds seconds and was stopped."
  }
  $process.Refresh()
  $state.terminal_exit_code = $process.ExitCode
  $common = Join-Path $env:PROGRAMDATA 'MetaQuotes\Terminal\Common\Files\NoraPhase0A'
  foreach ($name in @("${RunId}_trades.csv", "${RunId}_metrics.csv")) {
    $source = Join-Path $common $name
    if (-not (Test-Path $source)) { throw "Tester did not produce expected machine-readable artifact: $source" }
    Copy-Item -LiteralPath $source -Destination (Join-Path $runRoot $name) -Force
  }
  if (-not (Test-Path $reportPath)) { throw "Tester did not produce expected report: $reportPath" }
  $state.status = 'completed'; $state.completed_utc = (Get-Date).ToUniversalTime().ToString('o'); Write-State
}
catch {
  $state.status = 'failed'; $state.error = $_.Exception.Message; $state.completed_utc = (Get-Date).ToUniversalTime().ToString('o')
  if (Test-Path $runRoot) { Write-State }
  Write-Error $_
  exit 1
}
