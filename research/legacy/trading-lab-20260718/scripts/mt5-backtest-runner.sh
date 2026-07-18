#!/usr/bin/env bash
#
# mt5-backtest-runner.sh
# Runs a single MT5 Strategy Tester backtest via config-file mode (headless, no xdotool).
#
# Usage: mt5-backtest-runner.sh "<EA_name>" [output_dir]
#
# Author: Nora
# Date: 2026-07-08
#

set -euo pipefail

CONTAINER="MT5_Darwinex"
DISPLAY_NUM=":1"

# Backtest settings
SYMBOL="GDAXI"
TIMEFRAME="H1"           # PERIOD_H1
MODEL="1"                # 0=EveryTick1, 1=EveryTick, 2=1MinuteOHLC, 3=OpenPricesOnly
                         # Using 1 (Every Tick based on real ticks) — wait, let me use:
                         # Actually MT5 model IDs: 0=EveryTick1, 1=1MinuteOHLC, 2=OpenPricesOnly
                         # For "Every Tick" we want model 0 or use the GUI equivalent.
                         # In config mode: Model=0 is Every Tick, 1 is 1 minute OHLC, 3 is Open prices
                         # Let me use 0 for Every Tick
DEPOSIT="5000"
CURRENCY="USD"
LEVERAGE="20"            # 1:20
EXECUTION="1"            # 0=Random, 1=Realistic
DELAYS="10"              # milliseconds
START_DATE="2020.07.01"
END_DATE="2026.07.01"
FORWARD_DATE=""          # empty = no forward test
OPTIMIZATION="0"         # 0=disabled

# Input parameters (passed via .set file)
MM_LOTS="0.01"

# Paths inside container
MT5_BASE="/home/gasper/.wine/drive_c/Program Files/MetaTrader 5"
EA_DIR="${MT5_BASE}/MQL5/Experts/GDAXI"
REPORT_DIR_IN_CONTAINER="/home/gasper/backtest_reports"

# Take EA name from arg
EA_NAME="${1:?Usage: mt5-backtest-runner.sh <EA_name> [output_dir]}"
OUTPUT_DIR="${2:-/home/gasper/trading-lab/backtests/gdaxi_2020_07_01_2026_07_01}"

echo "[INFO] Starting proof backtest for: ${EA_NAME}"
echo "[INFO] Output dir: ${OUTPUT_DIR}"

# Create report dir inside container
docker exec "${CONTAINER}" bash -c "mkdir -p '${REPORT_DIR_IN_CONTAINER}'"

# Generate the .set file (EA input parameters) inside container
SET_FILE="${REPORT_DIR_IN_CONTAINER}/${EA_NAME}.set"
docker exec "${CONTAINER}" bash -c "cat > '${SET_FILE}' <<'EOFSET'
; Input parameters for ${EA_NAME}
mmLots=${MM_LOTS}
EOFSET"

# Generate the config INI file
CONFIG_FILE="${REPORT_DIR_IN_CONTAINER}/${EA_NAME}.ini"
REPORT_FILE="${EA_NAME}_report"
docker exec "${CONTAINER}" bash -c "cat > '${CONFIG_FILE}' <<'EOFINI'
[Tester]
Expert=\\\\Experts\\\\GDAXI\\\\${EA_NAME}.ex5
Symbol=${SYMBOL}
Period=${TIMEFRAME}
Deposit=${DEPOSIT}
Currency=${CURRENCY}
Leverage=${LEVERAGE}
Model=${MODEL}
Execution=${EXECUTION}
Delay=${DELAYS}
FromDate=${START_DATE}
ToDate=${END_DATE}
ForwardMode=0
Optimization=${OPTIMIZATION}
Visual=0
; Input parameters
InputsFile=${SET_FILE}
; Report output
Report=${REPORT_FILE}
ReplaceReport=1
ShutdownTerminal=1
EOFINI"

echo "[INFO] Config file written to: ${CONFIG_FILE}"

# Stop the watchdog temporarily so it doesn't restart terminal64 while we're running config mode
echo "[INFO] Pausing MT5 watchdog..."
docker exec "${CONTAINER}" bash -c "pkill -f mt5-watchdog.sh" 2>/dev/null || true
sleep 1

# Kill any running MT5 terminal
echo "[INFO] Stopping existing MT5 terminal..."
docker exec "${CONTAINER}" bash -c "su - gasper -c 'DISPLAY=${DISPLAY_NUM} wineserver -k' 2>/dev/null" || true
sleep 2
docker exec "${CONTAINER}" bash -c "su - gasper -c 'DISPLAY=${DISPLAY_NUM} taskkill /f /im terminal64.exe' 2>/dev/null" || true
sleep 2

# Run the backtest in config mode
echo "[INFO] Launching backtest via config mode..."
docker exec "${CONTAINER}" bash -lc "
    export DISPLAY=${DISPLAY_NUM}
    export WINEDEBUG=-all
    su - gasper -c 'export DISPLAY=${DISPLAY_NUM}; export WINEDEBUG=-all; cd \"${MT5_BASE}\"; wine terminal64.exe /config:\"${CONFIG_FILE}\"' &
    BACKTEST_PID=\$!
    echo \"[INFO] Backtest process PID: \${BACKTEST_PID}\"
"

# Wait for backtest to complete (max 30 minutes)
echo "[INFO] Waiting for backtest to complete (max 30 min)..."
MAX_WAIT=1800
WAITED=0
while [ ${WAITED} -lt ${MAX_WAIT} ]; do
    sleep 10
    WAITED=$((WAITED + 10))

    # Check if terminal64.exe is still running
    RUNNING=$(docker exec "${CONTAINER}" bash -c "ps aux | grep terminal64 | grep -v grep | wc -l")
    if [ "${RUNNING}" = "0" ]; then
        echo ""
        echo "[INFO] Backtest process finished."
        break
    fi
    echo -n "."
done
echo ""

if [ ${WAITED} -ge ${MAX_WAIT} ]; then
    echo "[ERROR] Timeout waiting for backtest to complete."
    docker exec "${CONTAINER}" bash -c "su - gasper -c 'DISPLAY=${DISPLAY_NUM} wineserver -k' 2>/dev/null" || true
fi

# Check for report file
echo "[INFO] Looking for report files..."
docker exec "${CONTAINER}" bash -c "ls -la '${REPORT_DIR_IN_CONTAINER}/' 2>/dev/null"
echo "---"
docker exec "${CONTAINER}" bash -c "find '${MT5_BASE}' -name '${REPORT_FILE}*' -newer '${CONFIG_FILE}' 2>/dev/null"
echo "---"
# MT5 sometimes saves reports in the Tester folder or the main directory
docker exec "${CONTAINER}" bash -c "find '${MT5_BASE}' -name '*report*' -newer '${CONFIG_FILE}' 2>/dev/null | head -10"

# Restart watchdog
echo "[INFO] Restarting MT5 watchdog..."
docker exec "${CONTAINER}" bash -c "su - gasper -c 'export DISPLAY=${DISPLAY_NUM}; nohup /home/gasper/.local/bin/mt5-watchdog.sh &' 2>/dev/null" || true

echo "[INFO] Proof backtest attempt complete for: ${EA_NAME}"
