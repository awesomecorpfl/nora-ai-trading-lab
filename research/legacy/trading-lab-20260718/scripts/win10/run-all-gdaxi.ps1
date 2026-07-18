# Batch runner for all 10 GDAXI backtests
# Runs each EA with 1-hour timeout, stores logs

$EAS = @(
    "GDAXI\Strategy 1.38.195",
    "GDAXI\Strategy 2.32.99",
    "GDAXI\Strategy 2.35.154",
    "GDAXI\Strategy 2.46.184",
    "GDAXI\Strategy 2.58.150",
    "GDAXI\Strategy 2.67.193",
    "GDAXI\Strategy 2.85.162",
    "GDAXI\Strategy 3.58.141",
    "GDAXI\Strategy 3.85.120",
    "GDAXI\Strategy 4.55.103"
)

$SCRIPT_PATH = "C:\Users\gasper\run-backtest.ps1"
$LOG_DIR = "C:\Users\gasper\backtest_logs"

New-Item -ItemType Directory -Force -Path $LOG_DIR | Out-Null

for ($i = 0; $i -lt $EAS.Count; $i++) {
    $EA = $EAS[$i]
    $LOG_FILE = Join-Path $LOG_DIR "bt_$($i+1)_$($EA -replace '\\', '_').log"

    Write-Host "========================================="
    Write-Host "Backtest $($i+1)/$($EAS.Count): $EA"
    Write-Host "========================================="

    # Timeout per backtest (seconds). H1 with Every Tick over 6 years takes significant time.
    # Estimate: ~30-90 minutes per test depending on data and strategy complexity.
    $TIMEOUT = 5400  # 90 minutes

    & powershell -ExecutionPolicy Bypass -File $SCRIPT_PATH `
        -FromDate 2020.07.01 -ToDate 2026.07.01 `
        -Expert $EA -TimeoutSec $TIMEOUT 2>&1 | Out-File $LOG_FILE -Encoding UTF8

    Write-Host "Completed. Log: $LOG_FILE"
    Write-Host ""

    # Small pause between backtests to let MT5 fully shut down
    Start-Sleep -Seconds 10
}

Write-Host "========================================="
Write-Host "All 10 backtests completed!"
Write-Host "========================================="
Write-Host "Logs directory: $LOG_DIR"