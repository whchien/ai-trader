from ai_trader.trader import AITrader
from ai_trader.strategy.base import BaseStrategy
from ai_trader.strategy.indicators import RSRS


class RSRSStrategy(BaseStrategy):
    """
    https://freewechat.com/a/MzkyODI5ODcyMA==/2247483898/1
    """

    params = dict(period=20, buy_threshold=0.8, close_threshold=0.5)

    def __init__(self):
        self.rsrs = RSRS(self.data, period=self.params.period)

    def next(self):
        buy_signal = self.rsrs.rsrs[0] > self.params.buy_threshold
        close_signal = self.rsrs.rsrs[0] < self.params.close_threshold

        if self.position.size == 0:
            if buy_signal:
                self.buy()
        else:
            if close_signal:
                self.close()


if __name__ == "__main__":
    trader = AITrader()
    trader.add_strategy(RSRSStrategy)
    trader.run()
    trader.plot()
