"""
Bollinger Bands Strategy

Implements a mean reversion strategy using Bollinger Bands to identify
overbought and oversold conditions based on price volatility.
"""

import backtrader as bt

from ai_trader.backtesting.strategies.base import BaseStrategy


class BBandsStrategy(BaseStrategy):
    """
    Bollinger Bands Strategy - Mean reversion based on volatility bands.

    Uses Bollinger Bands to identify potential entry and exit points based on
    the principle that prices tend to return to the mean after reaching extreme
    levels defined by standard deviation bands.

    Entry Logic (Buy):
    - Close price falls below the lower Bollinger Band (oversold condition)

    Exit Logic (Sell):
    - Close price rises above the upper Bollinger Band (overbought condition)

    Parameters:
    - period (int): Number of periods for moving average calculation [default: 20]
    - devfactor (float): Number of standard deviations for band width [default: 2]

    Notes:
    - Works best in ranging/consolidating markets; may generate false signals in strong trends
    - Standard devfactor of 2 captures approximately 95% of price action
    - Mean reversion strategies are counter-trend in nature
    """

    params = dict(period=20, devfactor=2)

    def __init__(self):
        """Initialize Bollinger Bands indicator with configured period and deviation factor."""
        self.bb = bt.indicators.BollingerBands(
            self.data, period=self.params.period, devfactor=self.params.devfactor
        )

    def next(self):
        """Execute trading logic based on price position relative to Bollinger Bands."""
        signal_buy = self.data.close[0] < self.bb.lines.bot[0]
        signal_sell = self.data.close[0] > self.bb.lines.top[0]

        if self.position.size == 0:
            if signal_buy:
                self.buy()

        if self.position.size > 0:
            if signal_sell:
                self.close()


if __name__ == "__main__":
    from ai_trader.utils.backtest import run_backtest

    # Run backtest with Bollinger Bands strategy
    results = run_backtest(
        strategy=BBandsStrategy,
        data_source=None,  # Use example data
        cash=1000000,
        commission=0.001425,
        strategy_params={"period": 20, "devfactor": 2.0},
    )

    print("\nBacktest completed! Use cerebro.plot() to visualize results.")
