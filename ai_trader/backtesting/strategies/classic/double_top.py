"""
Double Top Pattern Strategy

Detects double top reversal patterns and implements mean reversion trades
with time-based and signal-based exit conditions.
"""

from ai_trader.backtesting.strategies.base import BaseStrategy
from ai_trader.backtesting.strategies.indicators import DoubleTop


class DoubleTopStrategy(BaseStrategy):
    """
    Double Top Pattern Strategy - Mean reversion after double top formation.

    Identifies double top reversal patterns where price fails to break above a
    recent high twice, signaling potential downside reversal. Uses trend and
    volatility analysis to confirm pattern validity.

    Entry Logic (Buy):
    - Double Top indicator signal > 0 (pattern confirmed and price consolidated)

    Exit Logic (Sell):
    - Position held for maximum 30 days, or
    - Double Top indicator signal turns negative (pattern invalidated)

    Parameters:
    - sma_short (int): Short-term SMA period for trend analysis [default: 60]
    - sma_long (int): Long-term SMA period for trend analysis [default: 120]
    - vol_short (int): Short-term volatility period [default: 5]
    - vol_long (int): Long-term volatility period [default: 20]
    - past_highest (int): Lookback period for identifying recent highs [default: 60]

    Notes:
    - Time-based exit prevents position from staying open indefinitely
    - Requires confirmation from volatility and trend indicators
    - Double top is a reversal pattern; trades against the prior uptrend
    """

    params = dict(sma_short=60, sma_long=120, vol_short=5, vol_long=20, past_highest=60)

    def __init__(self):
        """Initialize Double Top pattern detector with trend and volatility parameters."""
        self.double_top = DoubleTop(
            self.data,
            sma_short=self.params.sma_short,
            sma_long=self.params.sma_long,
            vol_short=self.params.vol_short,
            vol_long=self.params.vol_long,
            past_highest=self.params.past_highest,
        )
        self.entry_date = None

        self.buy_signal = self.double_top.signal > 0

    def next(self):
        """Execute trading logic: enter on pattern signal, exit on time or signal reversal."""
        if self.position.size == 0:
            if self.buy_signal[0]:
                self.buy()
                self.entry_date = self.datetime.date(ago=0)

        else:
            holding_period = (self.datetime.date(ago=0) - self.entry_date).days

            # Close position after 30 days or if signal turns negative
            if holding_period > 30 or self.double_top.signal[0] < 0:
                self.close()
                self.entry_date = None


if __name__ == "__main__":
    from ai_trader.utils.backtest import run_backtest

    # Run backtest with DoubleTopStrategy
    results = run_backtest(
        strategy=DoubleTopStrategy,
        data_source=None,  # Use example data
        cash=1000000,
        commission=0.001425,
    )

    print("Backtest completed! Use cerebro.plot() to visualize results.")
