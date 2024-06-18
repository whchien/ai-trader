import backtrader as bt

from ai_trader.trader import AITrader
from ai_trader.strategy.base import BaseStrategy


class NaiveSMAStrategy(BaseStrategy):
    params = (("period", 15),)

    def __init__(self):
        self.sma = bt.indicators.MovingAverageSimple(
            self.data.close, period=self.params.period
        )
        self.signal_buy = self.data.close > self.sma
        self.signal_close = self.data.close < self.sma

    def next(self):
        # signal_buy = self.data.close[0] > self.sma[0]
        # signal_close = self.data.close[0] < self.sma[0]

        if not self.position:
            if self.signal_buy[0]:
                self.buy()

        else:
            if self.signal_close[0]:
                self.close()


class CrossSMAStrategy(BaseStrategy):
    params = (
        ("fast", 5),
        ("slow", 37),
    )

    def __init__(self):
        self.fast_ma = bt.indicators.SMA(
            self.data.close, period=self.params.fast, plotname="50_day_ma"
        )

        self.slow_ma = bt.indicators.SMA(
            self.data.close, period=self.params.slow, plotname="200_day_ma"
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
    engine = AITrader()
    engine.add_strategy(NaiveSMAStrategy)
    engine.run()
    engine.plot()
