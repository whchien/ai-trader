import backtrader as bt

from ai_trader.trader import AITrader
from ai_trader.strategy.base import BaseStrategy


class BollingerBandsStrategy(BaseStrategy):
    params = (("period", 20), ("devfactor", 2))

    def __init__(self):
        self.bb = bt.indicators.BollingerBands(
            self.data, period=self.params.period, devfactor=self.params.devfactor
        )
        self.order = None

    def next(self):
        if self.order:
            return

        signal_buy = self.data.close[0] < self.bb.lines.bot[0]
        signal_sell = self.data.close[0] > self.bb.lines.top[0]

        if self.position.size == 0:
            if signal_buy:
                self.buy()

        if self.position.size > 0:
            if signal_sell:
                self.close()


if __name__ == "__main__":
    engine = AITrader()
    engine.add_strategy(BollingerBandsStrategy)
    engine.run()
    engine.plot()
