#!/usr/bin/env python3
"""
Simple backtest example using utility functions.

This example shows how to run a quick backtest with the SMA strategy
using the convenience function.
"""

from ai_trader.backtesting.strategies.classic.sma import SMAStrategy
from ai_trader.utils.backtest import run_backtest

if __name__ == "__main__":
    # Run a complete backtest with one function call
    results = run_backtest(
        strategy=SMAStrategy,
        data_source=None,  # None = use example data
        cash=1000000,
        commission=0.001425,
        strategy_params={
            "fast_period": 10,
            "slow_period": 30,
        },
        sizer_params={"percents": 95},
        print_output=True,
    )

    print("\nBacktest completed successfully!")
