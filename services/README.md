# Supervisor service

The unit is deliberately not enabled by Phase 1. After creating the project virtual environment, install manually with `mkdir -p ~/.config/systemd/user && cp services/nora-lab-supervisor.service ~/.config/systemd/user/`, then run `systemctl --user daemon-reload` and `systemctl --user start nora-lab-supervisor`. Inspect with `journalctl --user -u nora-lab-supervisor`.

It has no secrets and does not interact with Hermes. Use `lab --root . supervisor --once` for the Phase 1 manual unit-path smoke test.
