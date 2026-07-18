#!/bin/bash
# Helper script to control the Windows VM for backtesting
# Usage: ./vm-helper.sh <start|stop|status|run>

set -e

VM_NAME="win10"
BOOT_WAIT=90  # seconds to wait for Windows boot
SHUTDOWN_WAIT=60  # seconds to wait for clean shutdown

case "$1" in
    start)
        echo "Starting VM: $VM_NAME"
        virsh start "$VM_NAME"
        echo "Waiting ${BOOT_WAIT}s for Windows boot..."
        sleep "$BOOT_WAIT"
        # Verify SSH is reachable
        until ssh -o ConnectTimeout=5 nora-win10 'exit 0' 2>/dev/null; do
            echo "Still booting... waiting 10s"
            sleep 10
        done
        echo "VM is ready"
        ;;

    stop)
        echo "Shutting down VM: $VM_NAME cleanly..."
        ssh nora-win10 'shutdown /s /t 5' 2>/dev/null || true
        echo "Waiting ${SHUTDOWN_WAIT}s for shutdown..."
        sleep "$SHUTDOWN_WAIT"

        # Verify it's actually off
        STATE=$(virsh list --all | grep "$VM_NAME" | awk '{print $3}')
        if [[ "$STATE" == "shut" ]]; then
            echo "VM is shut down"
        else
            echo "Warning: VM still showing as running, forcing shutdown"
            virsh destroy "$VM_NAME" || true
        fi
        ;;

    status)
        virsh list --all | grep "$VM_NAME"
        ;;

    run)
        # Start, wait for boot, and leave it running
        echo "Starting VM for backtesting session..."
        "$0" start
        echo ""
        echo "VM is ready. Run your backtest, then use: $0 stop"
        ;;

    *)
        echo "Usage: $0 {start|stop|status|run}"
        echo ""
        echo "Commands:"
        echo "  start   - Boot VM and wait for SSH to be ready"
        echo "  stop    - Clean shutdown via Windows, wait for poweroff"
        echo "  status  - Show VM state"
        echo "  run     - Start VM and leave it running (for interactive sessions)"
        exit 1
        ;;
esac