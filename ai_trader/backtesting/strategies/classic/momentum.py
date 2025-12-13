import backtrader as bt

from ai_trader.trader import AITrader
from ai_trader.backtesting.strategies.base import BaseStrategy


class MomentumStrategy(BaseStrategy):
    """
    https://en.wikipedia.org/wiki/Momentum_(technical_analysis)
    """

    params = dict(sma_period=50, momentum_period=14)

    def __init__(self):
        self.sma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.sma_period
        )
        self.momentum = bt.indicators.Momentum(
            self.data.close, period=self.params.momentum_period
        )
        self.buy_signal = self.momentum > 0
        self.close_signal = self.data.close < self.sma

    def next(self):
        if self.position.size == 0:
            if self.buy_signal[0]:
                self.buy()
        else:
            if self.close_signal[0]:
                self.close()


if __name__ == "__main__":
    trader = AITrader()
    trader.add_strategy(MomentumStrategy)
    trader.run()
    trader.plot()
