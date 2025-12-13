#!/usr/bin/env python3
"""
Pure Backtrader example without utilities.

This example shows how to use Backtrader directly without any helper functions,
demonstrating the full flexibility of the framework.
"""
import backtrader as bt

from ai_trader.backtesting.strategies.classic.rsi import RSIStrategy
from ai_trader.data.fetchers.base import load_example


class CustomStrategy(bt.Strategy):
    """Custom strategy defined inline."""

    params = (
        ("rsi_period", 14),
        ("oversold", 30),
        ("overbought", 70),
    )

    def __init__(self):
        self.rsi = bt.indicators.RSI(self.data.close, period=self.params.rsi_period)

    def next(self):
        if not self.position:
            # Buy when oversold
            if self.rsi < self.params.oversold:
                self.buy()
        else:
            # Sell when overbought
            if self.rsi > self.params.overbought:
                self.sell()


if __name__ == "__main__":
    # Create Cerebro
    cerebro = bt.Cerebro()

    # Configure broker
    cerebro.broker.setcash(1000000)
    cerebro.broker.setcommission(commission=0.001)

    # Load data
    df = load_example()
    data_feed = bt.feeds.PandasData(
        dataname=df,
        openinterest=None,
        timeframe=bt.TimeFrame.Days,
    )
    cerebro.adddata(data_feed)

    # Add strategy
    cerebro.addstrategy(CustomStrategy, rsi_period=14, oversold=30, overbought=70)

    # Add sizer
    cerebro.addsizer(bt.sizers.PercentSizer, percents=95)

    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
    cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")

    # Get initial value
    initial_value = cerebro.broker.getvalue()
    print(f"Starting Portfolio Value: ${initial_value:,.2f}")

    # Run backtest
    results = cerebro.run()

    # Get final value
    final_value = cerebro.broker.getvalue()
    print(f"Final Portfolio Value: ${final_value:,.2f}")

    # Extract results
    strat = results[0]

    # Print Sharpe Ratio
    sharpe = strat.analyzers.sharpe.get_analysis().get("sharperatio")
    if sharpe:
        print(f"Sharpe Ratio: {sharpe:.2f}")

    # Print Returns
    returns = strat.analyzers.returns.get_analysis()
    print(f"Total Return: {returns['rtot'] * 100:.2f}%")

    # Print Drawdown
    dd = strat.analyzers.drawdown.get_analysis()
    print(f"Max Drawdown: {dd['max']['drawdown']:.2f}%")

    # Print Trade Stats
    trades = strat.analyzers.trades.get_analysis()
    total_trades = trades.get("total", {}).get("total", 0)
    if total_trades > 0:
        won = trades.get("won", {}).get("total", 0)
        print(f"Total Trades: {total_trades}")
        print(f"Win Rate: {(won / total_trades) * 100:.1f}%")

    # Optional: Plot results
    # cerebro.plot()
