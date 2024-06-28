from ai_trader.strategy.indicators import RSRS
from ai_trader.trader import AITrader
from ai_trader.strategy.base import BaseStrategy


class RSRSRotationStrategy(BaseStrategy):
    """
    Implements the RSRS Rotation Strategy.

    References:
    - https://freewechat.com/a/MzkyODI5ODcyMA==/2247483898/1
    - https://mp.weixin.qq.com/s?__biz=MzIwNTU2ODMwNg==&mid=2247486024&idx=1&sn=e1dc5baa2894a15cfafe959d925f3ec1&chksm=972faa15a058230357dbd0dd9a4b700eff74f14e2d92494eb3b4f5b85d5c0a4bb77dfb1ab268&scene=21#wechat_redirect
    - https://mp.weixin.qq.com/s?__biz=MzIwNTU2ODMwNg==&mid=2247490664&idx=1&sn=ab95ea3a74977a1165fce280fc16ee38&chksm=961bdeef296e29a1f68094424a7f31804288e1d16c0d0b748e4ff7dfe85c6cdf6896158d1927&scene=132&exptype=timeline_recommend_article_extendread_samebiz&show_related_article=1&subscene=190&scene=132#wechat_redirect
    """

    params = dict(
        period=20,  # Momentum period
    )

    def __init__(self):
        # Indicator calculations
        self.inds = {data: RSRS(data, period=self.params.period) for data in self.datas}

    def next(self):
        to_buy, to_sell, holding = [], [], []

        for data, rsrs in self.inds.items():
            buy_signal = rsrs[0] > 1
            close_signal = rsrs[0] < 0.8

            if buy_signal:
                to_buy.append(data)
            if close_signal:
                to_sell.append(data)

            if self.getposition(data).size > 0:
                holding.append(data)

        # Close positions for data in to_sell list
        for sell in to_sell:
            if self.getposition(sell).size > 0:
                self.close(sell)

        # Update the list of holdings
        new_hold = list(set(to_buy + holding))
        for data in to_sell:
            if data in new_hold:
                new_hold.remove(data)

        if not new_hold:
            # New holdings list is empty
            return

        # Equal weight allocation
        # Existing positions should remain unchanged; cash should be equally allocated among new additions
        weight = 1 / len(new_hold)
        for data in new_hold:
            self.order_target_percent(data, weight)


if __name__ == "__main__":
    trader = AITrader()
    trader.add_strategy(RSRSRotationStrategy)
    trader.run()
    trader.plot()
