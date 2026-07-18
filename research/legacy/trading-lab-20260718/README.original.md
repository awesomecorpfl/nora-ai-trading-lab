# Trading Lab

Shared workspace for Nora & Gasper — backtesting, research, and analysis.

## Architecture

- **This machine (Fedora)**: Backtesting & research only. **No live trading.**
- **MT5 Docker container** (`MT5_Darwinex`): Strategy Tester backtests, Darwinex broker, investor (read-only) login.
- **Host Python** (`.venv`): Data analysis, backtest result processing, strategy research.
- **Live trading**: Happens on Windows VPS servers, not here.
- **Fusion Markets**: Separate container to be added when ready.

## Python Environment

```bash
source ~/trading-lab/.venv/bin/activate
```

Stack: pandas, numpy, scipy, scikit-learn, matplotlib, seaborn, plotly, vectorbt, backtrader, jupyterlab, openpyxl

## Directory Structure

```
trading-lab/
├── .venv/              # Python virtual environment
├── data/               # Market data (exports from MT5, downloads)
├── strategies/         # Strategy research & analysis code
├── backtests/          # Backtest results & reports
├── notes/              # Research notes & documentation
└── scripts/            # Utility scripts (data processing, etc.)
```

## MT5 Container

```bash
# VNC access (for Strategy Tester GUI)
# Connect to: localhost:5901

# Container management
docker start MT5_Darwinex
docker stop MT5_Darwinex
docker restart MT5_Darwinex
```

Image: `awesomecorpfl/mt5-desktop:v3`
Wine: 10.0
Persistent home: `~/docker/mt5/MT5_Darwinex-home`
Restart policy: `unless-stopped` (survives reboot)

Backup: Complete image + volume backup on Toshiba drive (6+ months old).
