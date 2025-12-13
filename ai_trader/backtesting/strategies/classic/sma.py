import backtrader as bt

from ai_trader.trader import AITrader
from ai_trader.backtesting.strategies.base import BaseStrategy


class NaiveSMAStrategy(BaseStrategy):
    params = dict(period=15)

    def __init__(self):
        self.sma = bt.indicators.MovingAverageSimple(
            self.data.close, period=self.params.period
        )
        self.signal_buy = self.data.close > self.sma
        self.signal_close = self.data.close < self.sma

    def next(self):
        if not self.position:
            if self.signal_buy[0]:
                self.buy()

        else:
            if self.signal_close[0]:
                self.close()


class CrossSMAStrategy(BaseStrategy):
    params = dict(fast=5, slow=37)

    def __init__(self):
        self.fast_ma = bt.indicators.SMA(
            self.data.close, period=self.params.fast, plotname="fast_day_ma"
        )

        self.slow_ma = bt.indicators.SMA(
            self.data.close, period=self.params.slow, plotname="slpw_day_ma"
        )
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)

    def next(self):
        if self.position.size == 0:
            if self.crossover > 0:
                self.buy()

        if self.position.size > 0:
            if self.crossover < 0:
                self.close()


if __name__ == "__main__":
    trader = AITrader()
    trader.add_strategy(CrossSMAStrategy)
    trader.run()
    trader.plot()
