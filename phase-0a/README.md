# Nora Phase 0A spike

Run `scripts/run_twice.sh` only after the data-control issue in [VERDICT.md](docs/VERDICT.md) is resolved. It deliberately fails loudly and confines VM writes to `C:\Users\Gasper\NoraPhase0A` plus `MQL5\Experts\NoraPhase0A` and `MQL5\Profiles\Tester\NoraPhase0A-*`.

`parse_and_compare.py` normalizes timestamp and ticket metadata before comparing trade semantics and decision metrics. Generated results are ignored by Git.

