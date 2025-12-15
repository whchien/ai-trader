"""
AI Trader - Backtesting framework for algorithmic trading strategies.

This package provides tools for backtesting trading strategies using Backtrader.

Quick Start:
    >>> from ai_trader.utils.backtest import run_backtest
    >>> from ai_trader.backtesting.strategies.classic.sma import SMAStrategy
    >>> results = run_backtest(SMAStrategy, data_source="data/AAPL.csv")

For more examples, see scripts/examples/ directory.
"""

__version__ = "0.3.0"

# Import main utilities for convenience
from ai_trader.utils.backtest import (
    run_backtest,
    create_cerebro,
    add_stock_data,
    add_portfolio_data,
    add_default_analyzers,
    add_analyzers,
    add_sizer,
    print_results,
)

__all__ = [
    "run_backtest",
    "create_cerebro",
    "add_stock_data",
    "add_portfolio_data",
    "add_default_analyzers",
    "add_analyzers",
    "add_sizer",
    "print_results",
]
