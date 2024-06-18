import backtrader as bt

from ai_trader.strategy.base import BaseStrategy
from ai_trader.strategy.indicators import DoubleTop
from ai_trader.trader import AITrader


class DoubleTopStrategy(BaseStrategy):
    def __init__(self):
        self.double_top = DoubleTop(self.data)
        self.sma_20 = bt.indicators.MovingAverageSimple(self.data.close, period=20)
        self.entry_date = None

        self.buy_signal = self.double_top.signal > 0
        self.close_signal = self.sma_20 < self.sma_20

    def next(self):
        if self.position.size == 0:
            if self.buy_signal[0]:
                self.buy()
                self.entry_date = self.datetime.date(ago=0)

        else:
            holding_period = (self.datetime.date(ago=0) - self.entry_date).days

            if self.close_signal[0] or holding_period > 30:
                self.close()
                self.entry_date = None


if __name__ == "__main__":
    engine = AITrader()
    engine.add_strategy(DoubleTopStrategy)
    # engine.add_strategy(BuyHoldStrategy)
    engine.run()
    engine.plot()
