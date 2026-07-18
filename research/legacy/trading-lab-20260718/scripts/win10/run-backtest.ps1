# MT5 Headless Backtest Runner for Windows VM
# Runs backtests via config-file mode (no GUI needed on native Windows)
# Usage: powershell -ExecutionPolicy Bypass -File run-backtest.ps1

param(
    [string]$FromDate,
    [string]$ToDate,
    [string]$Expert,
    [string]$Symbol = "GDAXI",
    [string]$Period = "H1",
    [int]$Deposit = 5000,
    [string]$Currency = "USD",
    [int]$Leverage = 20,
    [int]$Model = 0,
    [string]$ReportName = "",
    [int]$TimeoutSec = 7200
)

# Auto-generate report name from Expert name if not provided
if ([string]::IsNullOrWhiteSpace($ReportName)) {
    $safeExpert = $Expert.Replace('\', '_').Replace(' ', '_').Replace('.', '_')
    $ReportName = "Report_GDAXI_${safeExpert}.htm"
}

$MT5_DIR = "C:\\Program Files\\Darwinex MetaTrader 5"
$DATA_DIR = "C:\\Users\\gasper\\AppData\\Roaming\\MetaQuotes\\Terminal\\6C3C6A11D1C3791DD4DBF45421BF8028"

# Read credentials from existing common.ini
$commonIniPath = Join-Path $DATA_DIR "config\common.ini"
$commonContent = Get-Content -LiteralPath $commonIniPath -Raw
$envMatch = [regex]::Match($commonContent, 'Environment=([A-F0-9]+)')
$loginMatch = [regex]::Match($commonContent, 'Login=(\d+)')
$serverMatch = [regex]::Match($commonContent, 'Server=(.+)')

if (-not $envMatch.Success) {
    Write-Error "Could not find Environment hash in common.ini"
    exit 1
}

$environment = $envMatch.Groups[1].Value.Trim()
$login = $loginMatch.Groups[1].Value.Trim()
$server = $serverMatch.Groups[1].Value.Trim()

Write-Host "=== MT5 Backtest Runner ==="
Write-Host "Expert:    $Expert"
Write-Host "Symbol:    $Symbol"
Write-Host "Period:    $Period"
Write-Host "Deposit:   $Currency $Deposit"
Write-Host "Leverage:  1:$Leverage"
Write-Host "Model:     $Model (0=Every Tick)"
Write-Host "Date Range: $FromDate to $ToDate"
Write-Host "Report:    $ReportName"
Write-Host "Account:   $login @ $server"
Write-Host ""

# Build the config
$config = @"
[Common]
Environment=$environment
Login=$login
Server=$server
ProxyEnable=0
ProxyType=0
ProxyAddress=
EnableOpenCL=7
ProxyAuth=
CertInstall=0
NewsEnable=1
Services=4294967295
NewsLanguages=
Source=download.mql5.com

[Tester]
Expert=$Expert
Symbol=$Symbol
Period=$Period
Deposit=$Deposit
Currency=$Currency
Leverage=$Leverage
Model=$Model
ExecutionMode=0
Optimization=0
OptimizationCriterion=0
FromDate=$FromDate
ToDate=$ToDate
ForwardMode=0
Report=$ReportName
ReplaceReport=1
ShutdownTerminal=1
UseLocal=1
UseRemote=0
UseCloud=0
Visual=0
"@

# Write config as UTF-16LE (MT5 requirement)
$configPath = Join-Path $MT5_DIR "backtest_run.ini"
[System.IO.File]::WriteAllText($configPath, $config, [System.Text.Encoding]::Unicode)
Write-Host "Config written to: $configPath"

# Kill any running MT5 instance
Write-Host "Stopping any running MT5..."
Stop-Process -Name "terminal64" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Clear old logs
$logDir = Join-Path $MT5_DIR "logs"
if (Test-Path $logDir) {
    Get-ChildItem $logDir -Filter "*.log" | Where-Object { $_.LastWriteTime -lt (Get-Date).AddMinutes(-30) } | Remove-Item -Force -ErrorAction SilentlyContinue
}

# Clear cached .set files (MT5 caches EA inputs here, overrides compiled defaults)
$testerDir = Join-Path $DATA_DIR "MQL5\Profiles\Tester"
if (Test-Path $testerDir) {
    Write-Host "Clearing cached .set files from $testerDir..."
    Get-ChildItem $testerDir -Filter "*.set" | Remove-Item -Force -ErrorAction SilentlyContinue
}

# Launch MT5 with config
Write-Host "Launching MT5 with config..."
$startTime = Get-Date
$process = Start-Process -FilePath (Join-Path $MT5_DIR "terminal64.exe") `
    -ArgumentList "/config:backtest_run.ini" `
    -WorkingDirectory $MT5_DIR `
    -PassThru -WindowStyle Minimized

Write-Host "MT5 started (PID: $($process.Id))"
Write-Host "Waiting up to $TimeoutSec seconds for completion..."

# Wait for completion
$elapsed = 0
while (-not $process.HasExited -and $elapsed -lt $TimeoutSec) {
    Start-Sleep -Seconds 10
    $elapsed += 10
    if ($elapsed % 60 -eq 0) {
        Write-Host "  ...still running ($elapsed sec elapsed)"
    }
}

$endTime = Get-Date
$duration = ($endTime - $startTime).TotalSeconds

if (-not $process.HasExited) {
    Write-Host "TIMEOUT: Killing MT5 after $elapsed seconds"
    Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# Check for report - MT5 writes to AppData, not install dir
$reportPath = Join-Path $DATA_DIR $ReportName
if (Test-Path $reportPath) {
    Write-Host ""
    Write-Host "=== SUCCESS ==="
    Write-Host "Report: $reportPath"
    Write-Host "Duration: $([math]::Round($duration, 1)) seconds"
    Write-Host "Size: $((Get-Item $reportPath).Length) bytes"
} else {
    Write-Host ""
    Write-Host "=== NO REPORT FOUND ==="
    Write-Host "Expected: $reportPath"
    Write-Host "Checking for report in alternate locations..."
    Get-ChildItem -Path $DATA_DIR -Filter "Report*" -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "  $($_.Name) ($($_.Length) bytes)" }
}

# Show last log entries
Write-Host ""
Write-Host "=== Last log entries ==="
$logFile = Join-Path $logDir "$(Get-Date -Format 'yyyyMMdd').log"
if (Test-Path $logFile) {
    Get-Content -LiteralPath $logFile -Encoding Unicode -Tail 20 -ErrorAction SilentlyContinue
} else {
    # Try ASCII encoding
    Get-Content -LiteralPath $logFile -Tail 20 -ErrorAction SilentlyContinue
}

# Show tester log
$testerLogFile = Join-Path $MT5_DIR "Tester\logs\$(Get-Date -Format 'yyyyMMdd').log"
if (Test-Path $testerLogFile) {
    Write-Host ""
    Write-Host "=== Tester log ==="
    Get-Content -LiteralPath $testerLogFile -Encoding Unicode -Tail 20 -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "=== DONE ==="
