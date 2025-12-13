import backtrader as bt

from ai_trader.trader import AITrader
from ai_trader.backtesting.strategies.base import BaseStrategy


class BBandsStrategy(BaseStrategy):
    params = dict(period=20, devfactor=2)

    def __init__(self):
        self.bb = bt.indicators.BollingerBands(
            self.data, period=self.params.period, devfactor=self.params.devfactor
        )

    def next(self):
        signal_buy = self.data.close[0] < self.bb.lines.bot[0]
        signal_sell = self.data.close[0] > self.bb.lines.top[0]

        if self.position.size == 0:
            if signal_buy:
                self.buy()

        if self.position.size > 0:
            if signal_sell:
                self.close()


if __name__ == "__main__":
    trader = AITrader()
    trader.add_strategy(BBandsStrategy)
    trader.run()
    trader.plot()
