# Daily Notes

Status: working
Date: 2026-07-09
Time: 16:00

## Current focus
- Run 10 GDAXI backtests on the Windows VM using the headless script
- Collect and parse reports, extracting 7 metrics per EA
- Build summary CSV after completion

## What we were just doing
- Completed VM resource benchmarking: found sweetspot at 4 vCPUs / 8GB RAM
- Verified VM autostart is enabled at boot
- Updated maintenance script to gracefully shutdown VM before Sunday reboot
- Added VM to handoff.md for tracking
- Tested full cycle: destroy → start → boot → SSH ready (works perfectly)

## What is blocked
- None

## Active processes to stop
- pid: <add a real pid here when needed> | name: example process | restart: example restart command
- name: Windows VM (win10) | action: graceful shutdown | restart: virsh -c qemu:///session start win10

## Files or notes to carry forward
- vm-helper.sh at ~/trading-lab/scripts/vm-helper.sh for VM lifecycle
- Fixed run-backtest.ps1 at ~/trading-lab/scripts/win10/run-backtest.ps1
- Reports directory: ~/trading-lab/backtests/gdaxi_2020_07_01_2026_07_01/
- VM benchmark results: ~/trading-lab/vm-benchmark-settings.md
- Updated maintenance script: ~/.hermes/scripts/daily-nora-maintenance.sh

## What to restart after 08:00
- Nothing

## Next step for morning session
- Start VM with vm-helper.sh start (or let autostart handle it)
- Run backtest for the first EA
- Stop VM and verify report saved; repeat for all 10 EAs

## Notes
- VM name: win10, controlled via virsh -c qemu:///session
- VM config: 4 vCPUs / 8GB RAM (sweetspot - matches 6 vCPUs / 16GB performance)
- VM autostart: ENABLED - will boot automatically on host startup
- Backtest settings: Symbol=GDAXI, Period=H1, Deposit=$5000 USD, Leverage=1:20, Model=Every Tick, FromDate=2020.07.01, ToDate=2026.07.01
- mmLots=0.01 (handled by MT5 tester .set file cache)
- Metrics to extract: Net Profit, Max Equity DD%, Max Equity DD $, Total Trades, Win Rate%, Profit Factor, Return-to-DD Ratio
- Run backtests one at a time, sync each report to Fedora before the next run
- Use vm-helper.sh stop (graceful Windows shutdown) after each run; poll until VM is off
- Sunday maintenance script now gracefully shuts down VM before host reboot (uses `ssh nora-win10 'shutdown /s /t 5'`)