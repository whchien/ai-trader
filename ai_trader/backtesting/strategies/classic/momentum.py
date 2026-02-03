"""
Momentum Strategy

Combines momentum oscillator with trend filter to identify and trade
in the direction of positive price momentum.

Reference: https://en.wikipedia.org/wiki/Momentum_(technical_analysis)
"""

import backtrader as bt

from ai_trader.backtesting.strategies.base import BaseStrategy


class MomentumStrategy(BaseStrategy):
    """
    Momentum Strategy - Trend-following with momentum confirmation.

    Uses positive momentum (rate of change) combined with a trend filter
    to identify sustained uptrends. Momentum measures the velocity of price
    changes; positive momentum indicates accelerating price movements.

    Entry Logic (Buy):
    - Momentum indicator > 0 (positive rate of change over the period)

    Exit Logic (Sell):
    - Close price falls below the long-term simple moving average (trend reversal)

    Parameters:
    - sma_period (int): Period for trend confirmation SMA [default: 50]
    - momentum_period (int): Period for momentum calculation [default: 14]

    Notes:
    - Momentum measures: (Close - Close n periods ago) / Close n periods ago
    - Positive momentum suggests strength; entry waits for uptrend context
    - SMA acts as trend filter to avoid trading in downtrends
    - Works well in persistent trends; whipsaws in choppy markets
    """

    params = dict(sma_period=50, momentum_period=14)

    def __init__(self):
        """Initialize momentum oscillator and trend confirmation moving average."""
        self.sma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.sma_period)
        self.momentum = bt.indicators.Momentum(self.data.close, period=self.params.momentum_period)
        self.buy_signal = self.momentum > 0
        self.close_signal = self.data.close < self.sma

    def next(self):
        """Execute trading logic: buy on positive momentum, sell when price crosses below SMA."""
        if self.position.size == 0:
            if self.buy_signal[0]:
                self.buy()
        else:
            if self.close_signal[0]:
                self.close()


if __name__ == "__main__":
    from ai_trader.utils.backtest import run_backtest

    # Run backtest with MomentumStrategy
    results = run_backtest(
        strategy=MomentumStrategy,
        data_source=None,  # Use example data
        cash=1000000,
        commission=0.001425,
    )

    print("Backtest completed! Use cerebro.plot() to visualize results.")
