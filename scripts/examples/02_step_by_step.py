#!/usr/bin/env python3
"""
Step-by-step backtest example.

This example shows each step of the backtest process explicitly,
giving you full control over configuration.
"""
from ai_trader.backtesting.strategies.classic.bbands import BBandsStrategy
from ai_trader.utils.backtest import (
    add_default_analyzers,
    add_sizer,
    add_stock_data,
    create_cerebro,
    print_results,
)

if __name__ == "__main__":
    # Step 1: Create Cerebro with broker settings
    print("Step 1: Creating Cerebro instance...")
    cerebro = create_cerebro(cash=500000, commission=0.001)

    # Step 2: Add data
    print("Step 2: Loading stock data...")
    add_stock_data(
        cerebro,
        source=None,  # Use example data
        start_date="2020-01-01",
        end_date="2023-12-31",
    )

    # Step 3: Add strategy with parameters
    print("Step 3: Adding Bollinger Bands strategy...")
    cerebro.addstrategy(BBandsStrategy, period=20, devfactor=2.0)

    # Step 4: Add position sizer
    print("Step 4: Configuring position sizer...")
    add_sizer(cerebro, "percent", percents=90)

    # Step 5: Add analyzers
    print("Step 5: Adding performance analyzers...")
    add_default_analyzers(cerebro)

    # Step 6: Get initial value
    initial_value = cerebro.broker.getvalue()
    print(f"\nInitial portfolio value: ${initial_value:,.2f}")

    # Step 7: Run backtest
    print("\nRunning backtest...\n")
    results = cerebro.run()

    # Step 8: Get final value and print results
    final_value = cerebro.broker.getvalue()
    print_results(results, initial_value, final_value)

    print("\nBacktest completed!")
