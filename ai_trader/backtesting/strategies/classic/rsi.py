import backtrader as bt

from ai_trader.backtesting.strategies.base import BaseStrategy
from ai_trader.backtesting.strategies.indicators import TripleRSI


class RsiBollingerBandsStrategy(BaseStrategy):
    """
    Buy when the RSI is below 30 and the price is below the lower Bollinger Band.
    Sell when the RSI is above 70 or the price is above the upper Bollinger Band.
    """

    params = dict(rsi_period=14, bb_period=20, bb_dev=2, oversold=30, overbought=70)

    def __init__(self):
        self.rsi = bt.indicators.RSI(period=self.params.rsi_period)
        self.bbands = bt.indicators.BollingerBands(
            period=self.params.bb_period, devfactor=self.params.bb_dev
        )

    def next(self):
        buy_signal = (
            self.rsi < self.params.oversold and self.data.close[0] <= self.bbands.lines.bot[0]
        )
        close_signal = (
            self.rsi > self.params.overbought or self.data.close[0] >= self.bbands.lines.top[0]
        )

        if self.position.size == 0:
            if buy_signal:
                self.buy()
        else:
            if close_signal:
                self.close()


class TripleRsiStrategy(BaseStrategy):
    """
    Triple RSI Strategy - Multi-timeframe RSI confirmation with time-based exit.

    Uses three RSI indicators at different timeframes (short, medium, long) to
    generate high-confidence signals. Requires alignment across multiple timeframes
    for entry. Time-based exit prevents indefinite holding periods.

    Entry Logic (Buy):
    - TripleRSI signal > 0 (all three RSI indicators aligned bullishly)

    Exit Logic (Sell):
    - Close price falls below 60-period SMA (trend reversal) AND
    - Position held for minimum 60 days (time filter)

    Parameters:
    - rsi_short (int): Short-term RSI period [default: 20]
    - rsi_mid (int): Medium-term RSI period [default: 60]
    - rsi_long (int): Long-term RSI period [default: 120]
    - holding_period (int): Minimum holding period in days [default: 60]
    - oversold (int): RSI level for oversold condition [default: 55]
    - overbought (int): RSI level for overbought condition [default: 75]

    Notes:
    - TripleRSI synthesizes three timeframes to reduce false signals
    - Time-based exit (60 days) ensures position cycling and risk management
    - SMA trend filter prevents selling in early uptrend
    - Works well with buy-and-hold bias; filters mean-reversion trades
    """

    params = dict(
        rsi_short=20,
        rsi_mid=60,
        rsi_long=120,
        holding_period=60,
        oversold=55,
        overbought=75,
    )

    def __init__(self):
        """Initialize Triple RSI indicator across three timeframes and trend SMA."""
        self.rsi = TripleRSI(
            self.data.close,
            rsi_short=self.params.rsi_short,
            rsi_mid=self.params.rsi_mid,
            rsi_long=self.params.rsi_long,
            oversold=self.params.oversold,
            overbought=self.params.overbought,
        )
        self.sma = bt.indicators.MovingAverageSimple(self.data.close, period=60)
        self.entry_date = None

    def next(self):
        """Execute trading logic: buy on TripleRSI signal, sell on trend reversal after min holding period."""
        buy_signal = self.rsi > 0
        close_signal = self.data.close[0] < self.sma[0]

        if self.position.size == 0:
            if buy_signal:
                self.buy()
                self.entry_date = self.datetime.date(ago=0)
        else:
            holding_period = (self.datetime.date(ago=0) - self.entry_date).days

            # Calculate the holding period in days
            if close_signal and holding_period > self.params.holding_period:
                self.close()
                self.entry_date = None


if __name__ == "__main__":
    from ai_trader.utils.backtest import run_backtest

    # Run backtest with TripleRsiStrategy
    results = run_backtest(
        strategy=TripleRsiStrategy,
        data_source=None,  # Use example data
        cash=1000000,
        commission=0.001425,
    )

    print("Backtest completed! Use cerebro.plot() to visualize results.")
