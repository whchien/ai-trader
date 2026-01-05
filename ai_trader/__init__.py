"""
AI Trader - Backtesting framework for algorithmic trading strategies.

This package provides tools for backtesting trading strategies using Backtrader.

For more examples, see scripts/examples/ directory.
"""

__version__ = "0.3.0"

# Import main utilities for convenience
from ai_trader.utils.backtest import (
    add_analyzers,
    add_default_analyzers,
    add_portfolio_data,
    add_sizer,
    add_stock_data,
    create_cerebro,
    print_results,
    run_backtest,
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
