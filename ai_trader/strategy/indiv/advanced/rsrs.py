"""
https://mp.weixin.qq.com/s?__biz=MzIwNTU2ODMwNg==&mid=2247486024&idx=1&sn=e1dc5baa2894a15cfafe959d925f3ec1&chksm=972faa15a058230357dbd0dd9a4b700eff74f14e2d92494eb3b4f5b85d5c0a4bb77dfb1ab268&scene=21#wechat_redirect


To read more:
https://freewechat.com/a/MzkyODI5ODcyMA==/2247483898/1


"""

from ai_trader.trader import AITrader
from ai_trader.strategy.base import BaseStrategy
from ai_trader.strategy.indicators import RSRS


class RSRSStrategy(BaseStrategy):
    params = dict(
        period=20,
    )

    def __init__(self):
        self.rsrs = RSRS(self.data)

    def next(self):
        buy_signal = self.rsrs.rsrs[0] > 0.8
        close_signal = self.rsrs.rsrs[0] < 0.5

        if self.position.size == 0:
            if buy_signal:
                self.buy()
        else:
            if close_signal:
                self.close()


if __name__ == "__main__":
    engine = AITrader()
    engine.add_strategy(RSRSStrategy)
    engine.run()
    engine.plot()
