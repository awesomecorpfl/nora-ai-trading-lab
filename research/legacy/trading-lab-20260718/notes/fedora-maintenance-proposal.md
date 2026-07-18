# Fedora Nora Maintenance Proposal

Generated after inspecting:
- `/home/gasper/Documents/astrid-maintenance-scripts.tar.gz`
- current Fedora laptop paths/services/containers/remotes
- existing Hermes and trading-lab state

## What exists here

- Hermes CLI at `/home/gasper/.local/bin/hermes`
- Hermes gateway is a **user systemd service** managed by `hermes gateway start/stop`
- One MT5 Docker container: `MT5_Darwinex`
- MT5 bind mount: `/home/gasper/docker/mt5/MT5_Darwinex-home`
- Git repo: `/home/gasper/trading-lab`
- MEGA access via rclone remote: `nora_mega:`
- No evidence of local n8n deployment
- No evidence of local free-llm-gateway deployment
- No evidence of Cloudflare DDNS scripts/services on this laptop
- Telegram maintenance env file path chosen: `~/.backup-secrets/maintenance-telegram.env`
- No backup passphrase file yet: `~/.backup-secrets/nora-hermes-dr.pass`

Quick reference README:
- `~/.hermes/scripts/README-maintenance.md`

## Adapted scripts

- `~/.hermes/scripts/daily-handoff.py`
- `~/.hermes/scripts/daily-trading-lab-git-snapshot.sh`
- `~/.hermes/scripts/backup-nora-dr.sh`
- `~/.hermes/scripts/daily-nora-maintenance.sh`
- `~/.hermes/scripts/notify-maintenance-telegram.sh` (optional)
- `~/.hermes/scripts/post-reboot-maintenance-notify.sh`
- proposed cron file: `~/.hermes/scripts/fedora-maintenance-proposed.crontab`

## Proposed schedule

| Time | Schedule | Action |
|---|---|---|
| 7:15 | daily | write `handoff.md` freeze-frame |
| 7:20 | daily | git snapshot + push `~/trading-lab` |
| 7:30 | Mon-Sat | maintenance with `--no-reboot` |
| 7:30 | Sun | full maintenance + host OS update + reboot |
| @reboot | after Sunday reboot only | send post-reboot Telegram completion message if marker exists |
| 8:00 | separate Hermes behavior | fresh session reset |

## Backup coverage in `backup-nora-dr.sh`

### Included
- Hermes durable state:
  - `config.yaml`, `.env`, `auth.json`, `SOUL.md`
  - `state.db*`, `memory_store.db*`, `kanban.db*`
  - `memories/`, `skills/`, `plugins/`, `cron/`, `sessions/`, `scripts/`
  - selected metadata such as `channel_directory.json`, `gateway_state.json`
- `~/.config/rclone/rclone.conf`
- trading-lab lightweight state:
  - `.git/`, `.gitignore`, `README.md`
  - `current.md`, `handoff.md`
  - `notes/`, `scripts/`, `strategies/`
- MT5 lightweight restore set:
  - `MQL5/Experts`
  - `MQL5/Profiles`
  - `Config`

### Excluded intentionally
- `~/.hermes/hermes-agent` (1.1G runtime tree)
- `~/.hermes/node`, `bin`, `cache`, `logs`, `lsp`
- `~/trading-lab/.venv` (1.1G)
- `~/trading-lab/backtests`, `data`, `logs`
- full 3.8G MT5 bind mount caches/VNC/junk
- Docker images/layers/anonymous volumes
- n8n and free-llm-gateway data because they do not exist here
- Cloudflare DDNS assets because they do not exist here

## Validation already done

- shell syntax: `bash -n` passed on all new shell scripts
- backup dry-run succeeded and estimated included size around **38.3 MB**
- real encrypted backup upload succeeded to `nora_mega:Nora_Angel_Backups/disaster-recovery`
- remote stamped and latest backup objects both verified at **19,147,340 bytes**
- backup manifest now correctly includes MT5 `Experts`, `Profiles`, and `Config`
- git snapshot dry-run identified current staged candidates in `trading-lab`
- maintenance dry-run completed and showed the intended weekday flow
- Telegram notifier check mode passed and one real test message was sent successfully
- current notifier wording now uses:
  - weekday: `💜 Nora maintenance complete.`
  - post-reboot: `💜 Nora maintenance complete. Fedora rebooted.`
- current user crontab was **removed** so nothing is active yet

## Required before enablement

1. Create backup passphrase file:
   - `~/.backup-secrets/nora-hermes-dr.pass`
2. Telegram maintenance env file is already created:
   - `~/.backup-secrets/maintenance-telegram.env`
3. Sunday full backup/update/reboot is approved.
4. MT5 `Config/accounts.dat` is explicitly excluded from the DR kit for credential minimization.

## Suggestions

- Keep the lean DR kit exactly that: **identity + state + scripts + MT5 strategy/config subset**, not datasets or whole runtime trees.
- Keep weekday maintenance no-reboot; that matches the server’s intent without being annoying on a laptop.
- I recommend keeping the separate 7:20 git snapshot instead of bundling it only inside the maintenance job. It gives you one more recoverable layer before anything gets stopped.
- I would keep Telegram notifications optional until we confirm the bot/chat destination you actually want for machine alerts.
