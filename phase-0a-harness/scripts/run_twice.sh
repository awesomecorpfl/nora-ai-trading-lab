#!/usr/bin/env bash
set -euo pipefail
p=$(cd "$(dirname "${BASH_SOURCE[0]}")/.."&&pwd); out="$p/results/$(date -u +%Y%m%dT%H%M%SZ)";mkdir -p "$out";s=(ssh -F /dev/null -i "$HOME/.ssh/nora_win10" -p 2222 -o IdentitiesOnly=yes -o BatchMode=yes -o StrictHostKeyChecking=yes);c=(scp -F /dev/null -i "$HOME/.ssh/nora_win10" -P 2222 -o IdentitiesOnly=yes -o BatchMode=yes -o StrictHostKeyChecking=yes)
"${s[@]}" Gasper@127.0.0.1 'powershell.exe -NoProfile -Command "New-Item -ItemType Directory -Force -Path $env:USERPROFILE\\NoraMt5Harness\\incoming | Out-Null"';"${c[@]}" "$p/windows/run.ps1" Gasper@127.0.0.1:NoraMt5Harness/incoming/
for id in run1 run2;do "${s[@]}" Gasper@127.0.0.1 "powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\\Users\\Gasper\\NoraMt5Harness\\incoming\\run.ps1 -RunId $id";mkdir "$out/.${id}.partial";"${c[@]}" -r Gasper@127.0.0.1:NoraMt5Harness/runs/$id/\* "$out/.${id}.partial/";mv "$out/.${id}.partial" "$out/$id";done
python3 "$p/scripts/compare.py" "$out/run1/report.htm" "$out/run2/report.htm" "$out/comparison.json";echo "$out"
