import backtrader as bt

from ai_trader.trader import AITrader
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
            self.rsi < self.params.oversold
            and self.data.close[0] <= self.bbands.lines.bot[0]
        )
        close_signal = (
            self.rsi > self.params.overbought
            or self.data.close[0] >= self.bbands.lines.top[0]
        )

        if self.position.size == 0:
            if buy_signal:
                self.buy()
        else:
            if close_signal:
                self.close()


class TripleRsiStrategy(BaseStrategy):
    params = dict(
        rsi_short=20,
        rsi_mid=60,
        rsi_long=120,
        holding_period=60,
        oversold=55,
        overbought=75,
    )

    def __init__(self):
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
    trader = AITrader()
    trader.add_strategy(TripleRsiStrategy)
    trader.run()
    trader.plot()
