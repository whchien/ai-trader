"""
Simple Moving Average Strategies

Implements two trend-following strategies using simple moving averages:
1. Naive SMA: Price crossover above/below a single SMA
2. Cross SMA: Fast SMA crossover above/below slow SMA
"""

import backtrader as bt

from ai_trader.backtesting.strategies.base import BaseStrategy


class NaiveSMAStrategy(BaseStrategy):
    """
    Naive SMA Strategy - Price crossing a single moving average.

    Simple trend-following strategy that buys when price crosses above a simple
    moving average and sells when price falls below it. Responsive to short-term
    price movements but prone to whipsaws in choppy markets.

    Entry Logic (Buy):
    - Close price rises above the simple moving average

    Exit Logic (Sell):
    - Close price falls below the simple moving average

    Parameters:
    - period (int): Period for the simple moving average [default: 15]

    Notes:
    - Most basic SMA strategy; generates frequent signals
    - Prone to false signals during sideways/choppy markets
    - Works better on strong trending markets
    """

    params = dict(period=15)

    def __init__(self):
        """Initialize simple moving average indicator."""
        super().__init__()
        self.sma = bt.indicators.MovingAverageSimple(self.data.close, period=self.params.period)
        self.signal_buy = self.data.close > self.sma
        self.signal_close = self.data.close < self.sma

    def next(self):
        """Execute trading logic: buy above SMA, sell below SMA."""
        if not self.position:
            if self.signal_buy[0]:
                self.buy()

        else:
            if self.signal_close[0]:
                self.close()


class CrossSMAStrategy(BaseStrategy):
    """
    Cross SMA Strategy - Two SMA crossover strategy (MACD-like).

    Trend-following strategy that generates signals from the crossover of a
    fast (short-period) moving average and slow (long-period) moving average.
    More selective than Naive SMA; fewer but potentially higher-quality signals.

    Entry Logic (Buy):
    - Fast SMA crosses above slow SMA (bullish crossover / golden cross)

    Exit Logic (Sell):
    - Fast SMA crosses below slow SMA (bearish crossover / death cross)

    Parameters:
    - fast (int): Fast moving average period [default: 5]
    - slow (int): Slow moving average period [default: 37]

    Notes:
    - Golden cross (fast > slow) indicates uptrend; death cross indicates downtrend
    - Fewer false signals than single SMA due to confirmation from two MAs
    - Inherent lag due to MA smoothing; works better on longer timeframes
    """

    params = dict(fast=5, slow=37)

    def __init__(self):
        """Initialize fast and slow moving averages, and their crossover indicator."""
        super().__init__()
        self.fast_ma = bt.indicators.SMA(
            self.data.close, period=self.params.fast, plotname="fast_day_ma"
        )

        self.slow_ma = bt.indicators.SMA(
            self.data.close, period=self.params.slow, plotname="slpw_day_ma"
        )
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)

    def next(self):
        """Execute trading logic: buy on golden cross, sell on death cross."""
        if self.position.size == 0:
            if self.crossover > 0:
                self.buy()

        if self.position.size > 0:
            if self.crossover < 0:
                self.close()


if __name__ == "__main__":
    from ai_trader.utils.backtest import run_backtest

    # Run backtest with CrossSMAStrategy
    results = run_backtest(
        strategy=CrossSMAStrategy,
        data_source=None,  # Use example data
        cash=1000000,
        commission=0.001425,
        strategy_params={"fast": 5, "slow": 37},
    )

    print("\nBacktest completed! Use cerebro.plot() to visualize results.")
