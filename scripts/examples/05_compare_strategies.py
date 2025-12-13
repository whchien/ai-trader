#!/usr/bin/env python3
"""
Compare multiple strategies example.

This example shows how to run multiple strategies on the same data
and compare their performance.
"""
from ai_trader.backtesting.strategies.classic.bbands import BBandsStrategy
from ai_trader.backtesting.strategies.classic.buyhold import BuyHoldStrategy
from ai_trader.backtesting.strategies.classic.macd import MACDStrategy
from ai_trader.backtesting.strategies.classic.rsi import RSIStrategy
from ai_trader.backtesting.strategies.classic.sma import SMAStrategy
from ai_trader.utils.backtest import run_backtest


def run_and_collect_results(strategy_class, strategy_name, **strategy_params):
    """Run a backtest and collect key metrics."""
    print(f"\nRunning {strategy_name}...")

    results = run_backtest(
        strategy=strategy_class,
        data_source=None,  # Use example data
        cash=1000000,
        commission=0.001425,
        start_date="2020-01-01",
        end_date="2023-12-31",
        strategy_params=strategy_params,
        print_output=False,  # Don't print individual results
    )

    # Extract metrics
    strat = results[0]
    sharpe = strat.analyzers.sharpe.get_analysis().get("sharperatio")
    returns = strat.analyzers.returns.get_analysis()
    dd = strat.analyzers.drawdown.get_analysis()

    return {
        "strategy": strategy_name,
        "sharpe": sharpe if sharpe else 0,
        "total_return": returns.get("rtot", 0) * 100,
        "max_drawdown": dd.get("max", {}).get("drawdown", 0),
    }


if __name__ == "__main__":
    print("=" * 70)
    print("STRATEGY COMPARISON")
    print("=" * 70)

    # Define strategies to compare
    strategies = [
        (BuyHoldStrategy, "Buy & Hold", {}),
        (SMAStrategy, "SMA Crossover", {"fast_period": 10, "slow_period": 30}),
        (BBandsStrategy, "Bollinger Bands", {"period": 20, "devfactor": 2.0}),
        (RSIStrategy, "RSI", {"rsi_period": 14, "oversold": 30, "overbought": 70}),
        (MACDStrategy, "MACD", {}),
    ]

    # Run all strategies and collect results
    all_results = []
    for strategy_class, name, params in strategies:
        result = run_and_collect_results(strategy_class, name, **params)
        all_results.append(result)

    # Print comparison table
    print("\n" + "=" * 70)
    print("RESULTS COMPARISON")
    print("=" * 70)
    print(f"\n{'Strategy':<20} {'Sharpe':<10} {'Return %':<12} {'Max DD %':<10}")
    print("-" * 70)

    for result in all_results:
        print(
            f"{result['strategy']:<20} "
            f"{result['sharpe']:>8.2f}  "
            f"{result['total_return']:>10.2f}  "
            f"{result['max_drawdown']:>10.2f}"
        )

    # Find best strategy by Sharpe ratio
    best = max(all_results, key=lambda x: x["sharpe"])
    print("\n" + "=" * 70)
    print(f"Best Strategy (by Sharpe Ratio): {best['strategy']}")
    print(f"  Sharpe Ratio: {best['sharpe']:.2f}")
    print(f"  Total Return: {best['total_return']:.2f}%")
    print(f"  Max Drawdown: {best['max_drawdown']:.2f}%")
    print("=" * 70 + "\n")
