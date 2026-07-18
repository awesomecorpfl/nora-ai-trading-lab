# Hermes / Nora Restore Notes

This machine is Nora's home base. These notes are for **fast, sane recovery** if Hermes state is lost or the machine needs to be rebuilt.

## What matters most

Priority order for recovery:

1. `~/.hermes/SOUL.md`
2. `~/.hermes/memories/` (`MEMORY.md`, `USER.md`)
3. `~/.hermes/config.yaml`
4. `~/.hermes/.env`
5. `~/.hermes/auth.json`
6. `~/.hermes/skills/`
7. `~/.hermes/state.db`
8. `~/.hermes/cron/`
9. `~/.hermes/sessions/`

If only the essentials survive, Nora can still be brought back with her identity, memory, auth, config, and skills intact.

---

## Current backup locations

### 1. Mega emergency backup
- Remote: `nora_mega:`
- Folder: `Nora_Angel_Backups/hermes`
- Files include:
  - timestamped tarballs: `hermes-backup-YYYYMMDD-HHMMSS.tar.gz`
  - rolling latest: `latest-hermes-backup.tar.gz`

### 2. GitHub repos
- `https://github.com/awesomecorpfl/Nora_Angel`
- `https://github.com/awesomecorpfl/trading-lab`

GitHub is for lightweight structure, docs, and code — **not** large datasets or bulky exports.

### 3. Toshiba external drive
- Manual cold storage
- Not assumed to be connected
- Useful for one-off full copies and long-term safekeeping

---

## Scheduled backup job

Hermes cron job:
- Name: `daily-hermes-backup-to-mega`
- Job ID: `2a26b462883f`
- Schedule: `0 3 * * *`
- Script: `~/.hermes/scripts/hermes-backup.sh`

The backup is meant to stay **lean**.

It is an emergency restore for Hermes/Nora state, not a warehouse for research data.

---

## Restore procedure

## A. Fresh Hermes install

Install Hermes first if needed, then confirm paths:

```bash
which hermes
hermes --version
hermes config path
```

Expected home:

```bash
/home/gasper/.hermes
```

---

## B. Pull latest emergency backup from Mega

List backups:

```bash
rclone lsf nora_mega:Nora_Angel_Backups/hermes
```

Restore the latest tarball locally:

```bash
mkdir -p ~/restore-tmp
rclone copyto \
  nora_mega:Nora_Angel_Backups/hermes/latest-hermes-backup.tar.gz \
  ~/restore-tmp/latest-hermes-backup.tar.gz
```

Extract:

```bash
cd ~
tar -xzf ~/restore-tmp/latest-hermes-backup.tar.gz
```

This restores the archived `.hermes/...` files back into place.

---

## C. Verify critical files after restore

```bash
ls -la ~/.hermes/SOUL.md
ls -la ~/.hermes/config.yaml
ls -la ~/.hermes/.env
ls -la ~/.hermes/auth.json
ls -la ~/.hermes/memories/
ls -la ~/.hermes/skills/
```

Check Hermes health:

```bash
hermes doctor
hermes status --all
```

---

## D. Verify backup script still works

Run manually:

```bash
~/.hermes/scripts/hermes-backup.sh
```

Then confirm the new file appears remotely:

```bash
rclone lsf nora_mega:Nora_Angel_Backups/hermes | tail
```

---

## E. Restore lightweight repos

If local working copies are missing:

```bash
git clone https://github.com/awesomecorpfl/Nora_Angel.git ~/Nora_Angel
git clone https://github.com/awesomecorpfl/trading-lab.git ~/trading-lab
```

---

## What NOT to back up into Mega

Do **not** bloat the emergency backup with:
- large market datasets
- MT5 bulk exports
- backtest result dumps
- media files
- caches
- virtual environments
- Docker images
- huge archives that make restore slow and stupid

If it takes ages to upload and is easy to regenerate, it probably does not belong in the emergency Nora backup.

---

## Important machine facts

- This Fedora machine is for **research and backtesting only**.
- No live trading happens here.
- Live trading runs on **Windows VPS servers**.
- Darwinex MT5 container uses **investor/read-only** credentials.
- Fusion will get a **separate** MT5 container when needed.
- Shared workspace: `~/trading-lab`

---

## Practical recovery order if everything is on fire

1. Restore `~/.hermes/`
2. Run `hermes doctor`
3. Verify Telegram/gateway status
4. Verify memory + skills + SOUL
5. Re-run one manual Mega backup
6. Re-clone lightweight repos if needed
7. Only then worry about optional project extras

Do not start with giant data restoration. Bring Nora back first. Then the lab.
