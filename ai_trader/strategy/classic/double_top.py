import backtrader as bt

from ai_trader.strategy.base import BaseStrategy
from ai_trader.strategy.indicators import DoubleTop
from ai_trader.trader import AITrader


class DoubleTopStrategy(BaseStrategy):
    params = dict(sma_short=60, sma_long=120, vol_short=5, vol_long=20, past_highest=60)

    def __init__(self):
        self.double_top = DoubleTop(self.data)
        self.sma_20 = bt.indicators.MovingAverageSimple(
            self.data.close,
            sma_short=self.params.sma_short,
            sma_long=self.params.sma_long,
            vol_short=self.params.vol_short,
            vol_long=self.params.vol_long,
            past_highest=self.params.past_highest,
        )
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
    trader = AITrader()
    trader.add_strategy(DoubleTopStrategy)
    trader.run()
    trader.plot()
