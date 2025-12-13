#!/usr/bin/env python3
"""
Portfolio backtest example.

This example shows how to backtest a portfolio rotation strategy
across multiple stocks.
"""
from pathlib import Path

from ai_trader.backtesting.strategies.portfolio.roc_rotation import ROCRotationStrategy
from ai_trader.utils.backtest import (
    add_analyzers,
    add_portfolio_data,
    add_sizer,
    create_cerebro,
    print_results,
)

if __name__ == "__main__":
    # Check if data directory exists
    data_dir = Path("./data/tw_stock/")
    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}")
        print("Please create the directory and add stock CSV files.")
        exit(1)

    # Create Cerebro
    print("Creating portfolio backtest...")
    cerebro = create_cerebro(cash=2000000, commission=0.001425)

    # Load portfolio data
    print(f"Loading stocks from {data_dir}...")
    add_portfolio_data(
        cerebro,
        data_dir=data_dir,
        start_date="2020-01-01",
        end_date="2023-12-31",
        date_col="date",
    )

    # Add rotation strategy
    print("Adding ROC rotation strategy...")
    cerebro.addstrategy(
        ROCRotationStrategy,
        k=5,  # Select top 5 stocks
        rebalance_days=30,  # Rebalance monthly
        roc_period=20,  # ROC lookback period
    )

    # Add sizer - will divide capital among selected stocks
    add_sizer(cerebro, "percent", percents=95)

    # Add analyzers
    add_analyzers(cerebro, ["sharpe", "drawdown", "returns", "sqn"])

    # Run backtest
    initial_value = cerebro.broker.getvalue()
    print(f"\nStarting portfolio value: ${initial_value:,.2f}\n")

    results = cerebro.run()

    # Print results
    final_value = cerebro.broker.getvalue()
    print_results(results, initial_value, final_value)
