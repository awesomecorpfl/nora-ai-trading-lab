# Phase 0A MT5 validation harness

Run `scripts/run_twice.sh`. It stages only the Windows runner, launches the existing pinned broker-native configuration twice, transfers each completed run via a temporary `.partial` directory, and compares native MT5 HTML **Deals** and parsed metrics. Generated reports/configs are ignored by Git.

The runner fails closed unless MT5 exits and a fresh uniquely named report is copied from the terminal data root into the run directory.
