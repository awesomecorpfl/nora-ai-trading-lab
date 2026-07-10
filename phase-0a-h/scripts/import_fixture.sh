#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.."&&pwd); p="$root/phase-0a-h"; out="$p/results/import-$(date -u +%Y%m%dT%H%M%SZ)";mkdir -p "$out"
python3 "$p/scripts/generate_fixture.py" "$out/fixture.csv" >"$out/fixture.sha256"
s=(ssh -F /dev/null -i "$HOME/.ssh/nora_win10" -p 2222 -o IdentitiesOnly=yes -o BatchMode=yes -o StrictHostKeyChecking=yes);c=(scp -F /dev/null -i "$HOME/.ssh/nora_win10" -P 2222 -o IdentitiesOnly=yes -o BatchMode=yes -o StrictHostKeyChecking=yes)
"${s[@]}" Gasper@127.0.0.1 'powershell.exe -NoProfile -Command "New-Item -ItemType Directory -Force -Path $env:USERPROFILE\\NoraPhase0AH\\incoming | Out-Null"'
"${c[@]}" "$out/fixture.csv" "$p/ea/ImportFixture.mq5" "$p/config/import.template.ini" "$p/windows/import-fixture.ps1" Gasper@127.0.0.1:NoraPhase0AH/incoming/
"${s[@]}" Gasper@127.0.0.1 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\Users\Gasper\NoraPhase0AH\incoming\import-fixture.ps1 -IncomingRoot C:\Users\Gasper\NoraPhase0AH\incoming' | tee "$out/import-output.txt"
"${c[@]}" Gasper@127.0.0.1:NoraPhase0AH/import.json "$out/"
