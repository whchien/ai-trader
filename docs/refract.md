## Project Structure

```
ai-trader/
├── ai_trader/              # Main package
│   ├── data/                  # Data acquisition layer
│   │   ├── fetchers/          # Market & ephemeris data fetchers
│   │   │   ├── base.py        # Base market data fetcher
│   │   │   ├── crypto.py      # Cryptocurrency-specific fetcher
│   │   │   └── 
│   │   └── storage/           # File management (CSV/Parquet)
│   │       ├── base.py        # Base storage operations
│   │       └── 
│   ├── backtesting/           # Backtesting framework
│   │   ├── strategies/        # Trading strategies
│   │   ├── feeds/             # Custom data feeds
│   │   ├── analyzers/         # Performance analyzers
│   │   └── preparers/         # Data preparation
│   └── core/                  # Core utilities
│       ├── exceptions/        # Custom exceptions
│       └── utils.py           # Logging, config, progress tracking
├── config/                    # YAML configuration files
├── scripts/                   # Executable scripts
├── data/                      # Output data directory
├── ephemeris/                 # Swiss Ephemeris files
├── docs/                      # Documentation
└── notebooks/                 # Jupyter notebooks
```
