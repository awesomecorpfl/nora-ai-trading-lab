# Research and legacy archive

This directory is intentionally outside the active build paths (`engine/`, `lab/`,
`tests/`, and production `scripts/`). It contains historical research material and
retired workspace assets migrated from the former `/home/gasper/trading-lab` tree.

## Boundaries

- `backtests/` contains historical MT5 reports and result files. These are reference
  artifacts, not current acceptance evidence and are ignored by Git.
- `legacy/trading-lab-20260718/` contains the old workspace's scripts, notes, README,
  handoff, and VM benchmark records. The scripts are archived for reference only; do
  not call them as the canonical project runner without reviewing and promoting them
  into the active script surface.
- No Python virtual environment, generated logs, market-data dump, or Docker/Wine
  runtime was migrated. The old README describes a removed Docker/Wine stack and is
  retained only as historical context.

The canonical project remains `/home/gasper/nora-ai-trading-lab`. This archive must
not be imported by the Rust engine, Python control plane, test discovery, or evidence
qualification workflows.
