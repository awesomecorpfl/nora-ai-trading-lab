#!/usr/bin/env bash
#
# run-gdaxi-backtests.sh
# Runs backtests for all 10 GDAXI EAs via MT5 Strategy Tester GUI automation
#
# Symbol: GDAXI, TF: H1, Model: Every Tick
# Leverage: 1:20, Deposit: $5,000, Delays: 10ms
# Date: 2020.07.01 - 2026.07.01
# mmLots: 0.01
#
# Author: Nora
# Date: 2026-07-07
#

set -euo pipefail

# ============================================
# CONFIGURATION
# ============================================

CONTAINER_NAME="MT5_Darwinex"
DISPLAY_NUM=":1"
XDOTOOL_DELAY=1.2

# MT5 paths (inside container)
MT5_DIR="/home/gasper/.wine/drive_c/Program Files/MetaTrader 5"
EA_SOURCE_DIR="${MT5_DIR}/MQL5/Experts/GDAXI"
EA_COMPILED_DIR="${EA_SOURCE_DIR}"
REPORT_OUTPUT_DIR="/home/gasper/trading-lab/backtests/gdaxi_2020_07_01_2026_07_01"

# Backtest settings
SYMBOL="GDAXI"
TIMEFRAME="H1"
MODEL="Every Tick"
LEVERAGE="1:20"
DEPOSIT="5000"
DELAYS="10ms"
START_DATE="2020.07.01"
END_DATE="2026.07.01"
MM_LOTS="0.01"

# Report format
REPORT_FORMAT="html"  # Can be 'html' or 'csv'

# ============================================
# HELPER FUNCTIONS
# ============================================

# Check if container is running
container_is_running() {
    docker ps --filter "name=${CONTAINER_NAME}" --format '{{.Status}}' | grep -q "Up"
}

# Wait for MT5 terminal to be ready
mt5_ready() {
    docker exec "${CONTAINER_NAME}" bash -lc "ps aux | grep -v grep | grep terminal64" | grep -q "terminal64"
}

# Start container if not running
start_container() {
    if ! container_is_running; then
        echo "[INFO] Starting ${CONTAINER_NAME} container..."
        docker start "${CONTAINER_NAME}"
        sleep 10
    fi
}

# Open Strategy Tester from MT5
open_strategy_tester() {
    docker exec "${CONTAINER_NAME}" bash -lc "
        su - gasper -c '
            export DISPLAY=${DISPLAY_NUM}
            xdotool search --onlyvisible --name MetaTrader 5 windowactivate
            sleep ${XDOTOOL_DELAY}
            xdotool key --clearmodifiers Alt+F12
            sleep ${XDOTOOL_DELAY}
        '
    "
}

# Close Strategy Tester
close_strategy_tester() {
    docker exec "${CONTAINER_NAME}" bash -lc "
        su - gasper -c '
            DISPLAY=${DISPLAY_NUM}
            xdotool key --clearmodifiers Alt+F12
            sleep ${XDOTOOL_DELAY}
        '
    "
}

# Compile a single MQ5 file to EX5
compile_ea() {
    local ea_file="$1"
    local ea_name=$(basename "${ea_file}" .mq5)
    local compile_log="${REPORT_OUTPUT_DIR}/compile_${ea_name}.log"

    echo "[COMPILE] Compiling: ${ea_name}"

    docker exec "${CONTAINER_NAME}" bash -lc "
        su - gasper -c '
            export DISPLAY=${DISPLAY_NUM}
            xdotool search --onlyvisible --name MetaEditor windowactivate
            sleep ${XDOTOOL_DELAY}
            xdotool key --clearmodifiers ctrl+o
            sleep ${XDOTOOL_DELAY}
            xdotool type --delay 20 \"${EA_SOURCE_DIR}/${ea_name}\"
            xdotool key Return
            sleep 1
            xdotool key --clearmodifiers F7
            sleep 5
            import -window root /tmp/compile_result_${RANDOM}.png
        '
    " 2>&1 | tee "${compile_log}" || true

    # Check for compilation errors
    if ! grep -qi "no errors" "${compile_log}" 2>/dev/null; then
        echo "[WARN] Compilation had warnings or errors for: ${ea_name}"
        echo "       Check log: ${compile_log}"
    else
        echo "[OK] Compilation successful for: ${ea_name}"
    fi
}

# Run a single EA backtest
run_backtest() {
    local ea_file="$1"
    local ea_name=$(basename "${ea_file}" .mq5)
    local compiled_file="${EA_COMPILED_DIR}/${ea_name}.ex5"
    local report_file="${REPORT_OUTPUT_DIR}/${ea_name}_${START_DATE}_${END_DATE}.${REPORT_FORMAT}"

    echo "[START] Running backtest: ${ea_name}"

    # Check if compiled, if not compile first
    if [ ! -f "${compiled_file}" ]; then
        echo "[INFO] EA not compiled. Compiling..."
        compile_ea "${ea_file}"
        sleep 2

        # Verify compilation
        if [ ! -f "${compiled_file}" ]; then
            echo "[ERROR] Compilation failed or timed out for: ${ea_name}"
            return 1
        fi
    fi

    # Step 1: Open Strategy Tester
    open_strategy_tester
    sleep 2

    # Step 2: Open "Expert Advisors" tab
    docker exec "${CONTAINER_NAME}" bash -lc "
        su - gasper -c '
            export DISPLAY=${DISPLAY_NUM}
            xdotool key --clearmodifiers F3
            sleep ${XDOTOOL_DELAY}
        '
    "

    # Step 3: Clear EA path and type compiled EA name
    docker exec "${CONTAINER_NAME}" bash -lc "
        su - gasper -c '
            export DISPLAY=${DISPLAY_NUM}
            xdotool key --clearmodifiers Ctrl+a
            sleep 0.2
            xdotool type --delay 5 \"\"
            sleep ${XDOTOOL_DELAY}
        '
    "

    docker exec "${CONTAINER_NAME}" bash -lc "
        su - gasper -c '
            export DISPLAY=${DISPLAY_NUM}
            xdotool type --delay 10 \"${ea_name}\"
            sleep ${XDOTOOL_DELAY}
            xdotool key Return
            sleep 2
        '
    "

    # Step 4: Configure settings
    docker exec "${CONTAINER_NAME}" bash -lc "
        su - gasper -c '
            export DISPLAY=${DISPLAY_NUM}
            xdotool type --delay 10 \"${SYMBOL}\"
            sleep ${XDOTOOL_DELAY}
            xdotool key Return
            sleep 2
        '
    "

    docker exec "${CONTAINER_NAME}" bash -lc "
        su - gasper -c '
            export DISPLAY=${DISPLAY_NUM}
            xdotool type --delay 10 \"${TIMEFRAME}\"
            sleep ${XDOTOOL_DELAY}
            xdotool key Return
            sleep 2
        '
    "

    docker exec "${CONTAINER_NAME}" bash -lc "
        su - gasper -c '
            export DISPLAY=${DISPLAY_NUM}
            xdotool type --delay 10 \"${MODEL}\"
            sleep ${XDOTOOL_DELAY}
            xdotool key Return
            sleep 2
        '
    "

    docker exec "${CONTAINER_NAME}" bash -lc "
        su - gasper -c '
            export DISPLAY=${DISPLAY_NUM}
            xdotool type --delay 10 \"${LEVERAGE}\"
            sleep ${XDOTOOL_DELAY}
            xdotool key Return
            sleep 2
        '
    "

    docker exec "${CONTAINER_NAME}" bash -lc "
        su - gasper -c '
            export DISPLAY=${DISPLAY_NUM}
            xdotool type --delay 10 \"${DEPOSIT}\"
            sleep ${XDOTOOL_DELAY}
            xdotool key Return
            sleep 2
        '
    "

    docker exec "${CONTAINER_NAME}" bash -lc "
        su - gasper -c '
            export DISPLAY=${DISPLAY_NUM}
            xdotool type --delay 10 \"${DELAYS}\"
            sleep ${XDOTOOL_DELAY}
            xdotool key Return
            sleep 2
        '
    "

    docker exec "${CONTAINER_NAME}" bash -lc "
        su - gasper -c '
            export DISPLAY=${DISPLAY_NUM}
            xdotool type --delay 10 \"${START_DATE}\"
            sleep ${XDOTOOL_DELAY}
            xdotool key Return
            sleep 2
        '
    "

    docker exec "${CONTAINER_NAME}" bash -lc "
        su - gasper -c '
            export DISPLAY=${DISPLAY_NUM}
            xdotool type --delay 10 \"${END_DATE}\"
            sleep ${XDOTOOL_DELAY}
            xdotool key Return
            sleep 2
        '
    "

    # Step 5: Go to Input tab and set mmLots
    docker exec "${CONTAINER_NAME}" bash -lc "
        su - gasper -c '
            export DISPLAY=${DISPLAY_NUM}
            xdotool key --clearmodifiers Alt+I
            sleep ${XDOTOOL_DELAY}
        '
    "

    docker exec "${CONTAINER_NAME}" bash -lc "
        su - gasper -c '
            export DISPLAY=${DISPLAY_NUM}
            xdotool type --delay 10 \"${MM_LOTS}\"
            sleep ${XDOTOOL_DELAY}
            xdotool key Return
            sleep 2
        '
    "

    # Step 6: Start backtest
    docker exec "${CONTAINER_NAME}" bash -lc "
        su - gasper -c '
            export DISPLAY=${DISPLAY_NUM}
            xdotool key --clearmodifiers F5
            sleep 2
        '
    "

    # Step 7: Wait for backtest to complete
    echo "[INFO] Waiting for backtest to complete..."
    local max_wait=3600  # 1 hour max
    local waited=0
    while [ ${waited} -lt ${max_wait} ]; do
        sleep 10
        waited=$((waited + 10))

        # Check if Strategy Tester is still running
        if ! docker exec "${CONTAINER_NAME}" bash -lc "
            su - gasper -c '
                export DISPLAY=${DISPLAY_NUM}
                xdotool search --onlyvisible --name Strategy Tester
            '
        " | grep -q "Strategy Tester"; then
            echo "[INFO] Backtest completed."
            break
        fi

        echo -n "."
    done
    echo ""

    if [ ${waited} -ge ${max_wait} ]; then
        echo "[ERROR] Timeout waiting for backtest to complete. Giving up on ${ea_name}."
        return 1
    fi

    # Step 8: Save report
    docker exec "${CONTAINER_NAME}" bash -lc "
        su - gasper -c '
            export DISPLAY=${DISPLAY_NUM}
            xdotool key --clearmodifiers Alt+R
            sleep 1
            xdotool key --clearmodifiers F3
            sleep 1
            xdotool key --clearmodifiers F3
            sleep 1
            xdotool key --clearmodifiers Return
            sleep 2
        '
    "

    # Step 9: Wait for save dialog
    sleep 3

    # Step 10: Close Strategy Tester
    close_strategy_tester

    echo "[DONE] Backtest completed for: ${ea_name}"
    echo "       Report saved to: ${report_file}"

    # Copy report from container to host
    docker cp "${CONTAINER_NAME}:${EA_COMPILED_DIR}/${ea_name}_${START_DATE}_${END_DATE}.${REPORT_FORMAT}" "${report_file}"
    echo "[INFO] Copied report to host: ${report_file}"
}

# ============================================
# MAIN
# ============================================

main() {
    echo "=========================================="
    echo "GDAXI Backtest Runner"
    echo "=========================================="
    echo "Date range: ${START_DATE} - ${END_DATE}"
    echo "Symbol: ${SYMBOL}"
    echo "Timeframe: ${TIMEFRAME}"
    echo "Model: ${MODEL}"
    echo "Leverage: ${LEVERAGE}"
    echo "Deposit: ${DEPOSIT}"
    echo "mmLots: ${MM_LOTS}"
    echo "=========================================="

    # Ensure output directory exists
    mkdir -p "${REPORT_OUTPUT_DIR}"

    # Ensure container is running
    start_container

    # Wait for MT5 to be ready
    echo "[INFO] Waiting for MT5 terminal to be ready..."
    local retry=0
    while ! mt5_ready && [ ${retry} -lt 30 ]; do
        sleep 2
        retry=$((retry + 1))
        echo -n "."
    done
    echo ""

    if ! mt5_ready; then
        echo "[ERROR] MT5 terminal is not ready. Please start it manually and try again."
        exit 1
    fi

    echo "[INFO] MT5 terminal is ready. Starting backtests..."

    # Get list of EA files
    mapfile -t EAS < <(ls -1 "${EA_SOURCE_DIR}"/*.mq5 2>/dev/null || echo "")

    if [ ${#EAS[@]} -eq 0 ]; then
        echo "[ERROR] No EA files found in ${EA_SOURCE_DIR}"
        exit 1
    fi

    echo "[INFO] Found ${#EAS[@]} EA files to backtest."
    echo ""

    # Run each EA
    local failed=0
    local passed=0

    for ea in "${EAS[@]}"; do
        if run_backtest "${ea}"; then
            passed=$((passed + 1))
        else
            failed=$((failed + 1))
        fi
        echo ""
    done

    echo "=========================================="
    echo "Summary:"
    echo "  Passed: ${passed}"
    echo "  Failed: ${failed}"
    echo "=========================================="

    if [ ${failed} -gt 0 ]; then
        echo "[WARN] Some backtests failed. Check the logs above for details."
    fi
}

main "$@"
