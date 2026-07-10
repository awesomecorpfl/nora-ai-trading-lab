#!/usr/bin/env bash
set -euo pipefail
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
phase="$repo_root/phase-0a"
host=${NORA_MT5_HOST:-127.0.0.1}
port=${NORA_MT5_PORT:-2222}
user=${NORA_MT5_USER:-Gasper}
key=${NORA_MT5_KEY:-$HOME/.ssh/nora_win10}
ssh_base=(ssh -F /dev/null -i "$key" -p "$port" -o IdentitiesOnly=yes -o BatchMode=yes -o ConnectTimeout=15 -o StrictHostKeyChecking=yes)
scp_base=(scp -F /dev/null -i "$key" -P "$port" -o IdentitiesOnly=yes -o BatchMode=yes -o StrictHostKeyChecking=yes)
remote="$user@$host"
stamp=$(date -u +%Y%m%dT%H%M%SZ)
result_root="$phase/results/$stamp"
mkdir -p "$result_root"
"${ssh_base[@]}" "$remote" 'powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "New-Item -ItemType Directory -Force -Path $env:USERPROFILE\\NoraPhase0A\\incoming | Out-Null"'
"${scp_base[@]}" "$phase/ea/Phase0Probe.mq5" "$phase/config/tester.template.ini" "$phase/config/probe.set.template" "$phase/windows/run-phase0a.ps1" "$remote:NoraPhase0A/incoming/"
for run in run1 run2; do
  "${ssh_base[@]}" "$remote" "powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\\Users\\$user\\NoraPhase0A\\incoming\\run-phase0a.ps1 -RunId $run -IncomingRoot C:\\Users\\$user\\NoraPhase0A\\incoming"
  "${scp_base[@]}" -r "$remote:NoraPhase0A/runs/$run" "$result_root/"
done
python3 "$phase/scripts/parse_and_compare.py" "$result_root/run1" "$result_root/run2" "$result_root/comparison.json"
printf 'Phase 0A results: %s\n' "$result_root"

