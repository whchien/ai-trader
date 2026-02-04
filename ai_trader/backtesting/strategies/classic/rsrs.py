"""
RSRS (Rising/Sinking Support and Resistance) Strategy

Identifies trend strength based on support and resistance line slopes.

Reference: https://freewechat.com/a/MzkyODI5ODcyMA==/2247483898/1
"""

from ai_trader.backtesting.strategies.base import BaseStrategy
from ai_trader.backtesting.strategies.indicators import RSRS


class RSRSStrategy(BaseStrategy):
    """
    RSRS Strategy - Trend strength analysis via support/resistance slopes.

    RSRS measures the slopes of support (low point trendline) and resistance
    (high point trendline) to quantify trend strength. Higher RSRS values indicate
    stronger uptrends with steeper resistance slopes, suggesting bullish momentum.

    Entry Logic (Buy):
    - RSRS indicator > 0.8 (strong uptrend confirmed)

    Exit Logic (Sell):
    - RSRS indicator < 0.5 (trend strength weakening)

    Parameters:
    - period (int): Number of periods for calculating support/resistance lines [default: 20]
    - buy_threshold (float): RSRS level to trigger buy signal [default: 0.8]
    - close_threshold (float): RSRS level to trigger exit [default: 0.5]

    Notes:
    - RSRS > 1.0 typically indicates very strong uptrends
    - RSRS < 0.0 often indicates downtrends
    - Buy threshold of 0.8 requires solid uptrend confirmation
    - Close threshold of 0.5 exits before trend reversal accelerates
    """

    params = dict(period=20, buy_threshold=0.8, close_threshold=0.5)

    def __init__(self):
        """Initialize RSRS indicator with configured period."""
        self.rsrs = RSRS(self.data, period=self.params.period)

    def next(self):
        """Execute trading logic: buy on strong uptrend, sell when trend weakens."""
        buy_signal = self.rsrs.rsrs[0] > self.params.buy_threshold
        close_signal = self.rsrs.rsrs[0] < self.params.close_threshold

        if self.position.size == 0:
            if buy_signal:
                self.buy()
        else:
            if close_signal:
                self.close()


if __name__ == "__main__":
    from ai_trader.utils.backtest import run_backtest

    # Run backtest with RSRSStrategy
    results = run_backtest(
        strategy=RSRSStrategy,
        data_source=None,  # Use example data
        cash=1000000,
        commission=0.001425,
    )

    print("Backtest completed! Use cerebro.plot() to visualize results.")
