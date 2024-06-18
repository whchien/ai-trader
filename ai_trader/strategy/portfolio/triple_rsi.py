"""
RSI黃金交叉死亡交叉的選股買賣，效果非常不好，甚至落後大盤。
所以撇除黃金交叉等用法，實驗證明 RSI 絕對數值是有效能夠找出動能的強弱，
我們用 RSI 長中短週期來進行選股，會有不錯的效果。

此策略主要進場條件為長週期 RSI 指標轉強。
主要進場條件為股價跌破季線，RSI 短線不過熱，
中長線穩定發揮時，適合持有。
每週換股。
"""

import backtrader as bt

from ai_trader.trader import AITrader
from ai_trader.strategy.base import BaseStrategy
from ai_trader.strategy.indicators import TripleRSI


class TripleRSIStrategy(BaseStrategy):
    """
    https://zhuanlan.zhihu.com/p/269443883

    """

    params = dict(
        rebal_month=[2, 4, 6, 8, 10, 12],
        rebal_monthday=[5],  # 每月1日执行再平衡
        num_volume=5,  # 成交量取前100名
    )

    def __init__(self):
        self.indicators = {data: TripleRSI(data) for data in self.datas}
        self.order_list = []
        self.last_buy = []  # 上次交易股票的列表

        # 定时器
        # Schedules a timer to invoke notify_timer
        self.add_timer(
            when=bt.Timer.SESSION_START,
            monthdays=self.p.rebal_monthday,  # 每月1号触发再平衡
            monthcarry=True,  # 若再平衡日不是交易日，则顺延触发notify_timer
        )

    def notify_timer(self, timer, when, *args, **kwargs):
        self.rebalance()

        # # 只在5，9，11月的1号执行再平衡
        # if self..data.datetime.date(0).month in self.params.rebal_month:
        #     self.rebalance()  # 执行再平衡

    def next(self):
        pass

    def rebalance(self):
        # 从指数取得当前日期
        current_date = self.data0.datetime.date(0)
        self.log(f"Rebalance date: {current_date}")

        # 如果是指数的最后一本bar，则退出，防止取下一日开盘价越界错
        if len(self.datas[0]) == self.data0.buflen():
            return

        # 取消以往所下订单（已成交的不会起作用）
        for o in self.order_list:
            self.cancel(o)

        self.order_list = []  # 重置订单列表

        # 1 先做排除筛选过程
        to_buy = [data for data, rsi in self.indicators.items() if rsi.signal[0] > 0]

        if len(to_buy) == 0:  # 无股票选中，则返回
            self.log("No target stocks found...")
            return

        # 2 再做排序挑选过程
        to_buy.sort(key=lambda d: d.volume, reverse=True)  # 按成交量从大到小排序
        to_buy = to_buy[: self.params.num_volume]  # 取前num_volume名

        # 3 以往买入的标的，本次不在标的中，则先平仓
        to_close = set(self.last_buy) - set(to_buy)
        for data in to_close:
            self.log(f"Leave: {data._name} | Size: {self.getposition(data).size}")
            o = self.close(data=data)
            self.order_list.append(o)  # 记录订单

        # 4 本次标的下单
        # 每只股票买入资金百分比，预留2%的资金以应付佣金和计算误差
        weight = (1 - 0.02) / len(to_buy)

        # 得到目标市值
        target_value = weight * self.broker.getvalue()

        # 为保证先卖后买，股票要按持仓市值从大到小排序
        to_buy.sort(key=lambda d: self.broker.getvalue([d]), reverse=True)
        self.log(
            f"Order - target_number: {len(to_buy)} |"
            f"target_value: {target_value} |"
            f"current_ttl_value: {self.broker.getvalue()}"
        )

        for data in to_buy:
            if data in self.last_buy:
                self.log("Rebal {} ".format(data._name))
                o = self.order_target_percent(data, target=weight * 0.95)
                self.order_list.append(o)
            else:
                self.log("Enter {} ".format(data._name))
                o = self.order_target_percent(data, target=weight * 0.95)
                self.order_list.append(o)

            # # 按次日开盘价计算下单量，下单量是100的整数倍
            # size = int(
            #     abs((self.broker.getvalue([.data]) - target_value) / .data.open[1] // 100 * 100)
            # )
            # valid_day = .data.datetime.datetime(1)  # 该股下一实际交易日
            # if self.broker.getvalue([.data]) > target_value:  # 持仓过多，要卖
            #     # 次日跌停价近似值
            #     lowest_price = .data.close[0] * 0.9 + 0.02
            #
            #     o = self.sell(
            #         .data=.data,
            #         size=size,
            #         exectype=bt.Order.Market,
            #         # price=lowest_price,
            #         valid=valid_day,
            #     )
            # else:  # 持仓过少，要买
            #     # 次日涨停价近似值
            #     upper_price = .data.close[0] * 1.1 - 0.02
            #     o = self.buy(
            #         .data=.data,
            #         size=size,
            #         exectype=bt.Order.Market,
            #         # price=upper_price,
            #         valid=valid_day,
            #     )
            #
            # self.order_list.append(o)  # 记录订单

        self.last_buy = to_buy  # 跟踪上次买入的标的


if __name__ == "__main__":
    e = AITrader()
    e.cerebro.addstrategy(TripleRSIStrategy)
    e.run(data_type="portfolio", sizer=False)
    e.cerebro.plot(volume=False)
