import backtrader as bt

from ai_trader.trader import AITrader
from ai_trader.backtesting.strategies.base import BaseStrategy


class TurtleTradingStrategy(BaseStrategy):
    """
    In the Turtle Trading strategy, ATR is often used as a measure of volatility to determine position size and stop
    levels. Traders adjust their position size based on the current volatility, aiming to risk a consistent
    percentage of their trading capital on each trade. Additionally, ATR is used to set stop-loss levels dynamically,
    ensuring that stops are placed at levels that reflect the current market conditions.

    Read more:
    https://medium.com/@jesso1908joy/testing-turtle-trading-strategy-in-backtrader-b3a6e2075703

    """

    params = dict(
        long_period=20,  # Period for the upper Donchian channel
        short_period=10,  # Period for the lower Donchian channel
    )

    def __init__(self):
        self.order = None
        self.buy_count = 0
        self.last_price = 0

        self.close = self.datas[0].close
        self.high = self.datas[0].high
        self.low = self.datas[0].low

        # Calculate the upper Donchian channel: the highest price of the past 20 days
        self.donchian_high = bt.ind.Highest(
            self.high(-1), period=self.p.long_period, subplot=True
        )

        # Calculate the lower Donchian channel: the lowest price of the past 10 days
        self.donchian_low = bt.ind.Lowest(
            self.low(-1), period=self.p.short_period, subplot=True
        )

        # Generate upper Donchian channel entry breakout: close > DonchianH, value is 1.0; otherwise -1.0
        self.cross_high = bt.ind.CrossOver(
            self.close(0), self.donchian_high, subplot=False
        )

        # Generate lower Donchian channel exit breakdown: close < DonchianL, value is 1.0; otherwise -1.0
        self.cross_low = bt.ind.CrossOver(
            self.close(0), self.donchian_low, subplot=False
        )

        # True Range (TR): True Range is a measure of volatility that takes into account the price range of an
        # asset over a certain period. It considers the following three values: The current high minus the current
        # low. The absolute value of the current high minus the previous close. The absolute value of the current low
        # minus the previous close.
        self.TR = bt.ind.Max(
            (self.high(0) - self.low(0)),  # Current day's high minus current day's low
            abs(
                self.high(0) - self.close(-1)
            ),  # abs(current day's high - previous day's close)
            abs(
                self.low(0) - self.close(-1)
            ),  # abs(current day's low - previous day's close)
        )

        # self.ATR = bt.ind.MovingAverageSimple(self.TR, period=self.p.entry_breakout, subplot=False)

        # Calculate ATR using talib. Install with python3 -m pip install TA-Lib
        self.ATR = bt.talib.ATR(
            self.high, self.low, self.close, timeperiod=self.p.long_period, subplot=True
        )

    def next(self):
        if self.order:
            return

        # If currently holding a long position
        if self.position.size > 0:
            # Add to long position:
            # price rises by 0.5 ATR from the buy price and the number of additions <= 3
            if (
                self.datas[0].close > self.last_price + 0.5 * self.ATR[0]
                and self.buy_count <= 4
            ):
                buy_unit = max((self.broker.getvalue() * 0.01) / self.ATR[0], 1)
                self.order = self.buy(size=int(buy_unit))
                self.last_price = self.position.price
                self.buy_count = self.buy_count + 1

            # Long position stop loss:
            # stop out when the price falls by 2 ATR
            elif self.datas[0].close < (self.last_price - 2 * self.ATR[0]):
                self.order = self.sell(size=abs(self.position.size))
                self.buy_count = 0

            # Long position take profit:
            # take profit and close the position when the price breaks below the 10-day low
            elif self.cross_low < 0:
                self.order = self.sell(size=abs(self.position.size))
                self.buy_count = 0

        # If no position is held, wait for the entry opportunity
        else:
            # Entry: go long when the price breaks the upper channel and no position is held
            if self.cross_high > 0 and self.buy_count == 0:
                buy_unit = int(max((self.broker.getvalue() * 0.01) / self.ATR[0], 1))
                self.order = self.buy(size=buy_unit)
                self.last_price = self.position.price  # Record the purchase price
                self.buy_count = 1  # Record the price of this transaction


if __name__ == "__main__":
    trader = AITrader()
    trader.add_strategy(TurtleTradingStrategy)
    trader.run()
    trader.plot()
