import math

import backtrader as bt
import numpy as np

from ai_trader.trader import AITrader
from ai_trader.strategy.base import BaseStrategy


class TurtleTradingStrategy(BaseStrategy):
    """
    In the Turtle Trading strategy, ATR is often used as a measure of volatility to determine position size and stop
    levels. Traders adjust their position size based on the current volatility, aiming to risk a consistent
    percentage of their trading capital on each trade. Additionally, ATR is used to set stop-loss levels dynamically,
    ensuring that stops are placed at levels that reflect the current market conditions.

    https://medium.com/@jesso1908joy/testing-turtle-trading-strategy-in-backtrader-b3a6e2075703

    """

    params = dict(
        N1=20,  # 唐奇安通道上轨的t
        N2=10,  # 唐奇安通道下轨的t
    )

    def __init__(self):
        self.order = None
        self.buy_count = 0  # 记录买入次数
        self.last_price = 0  # 记录买入价# 格

        self.close = self.datas[0].close
        self.high = self.datas[0].high
        self.low = self.datas[0].low

        # 计算唐奇安通道上轨：过去20日的最高价
        self.donchian_high = bt.ind.Highest(
            self.high(-1), period=self.p.N1, subplot=True
        )

        # 计算唐奇安通道下轨：过去10日的最低价
        self.donchian_low = bt.ind.Lowest(self.low(-1), period=self.p.N2, subplot=True)

        # 生成唐奇安通道上轨突破：close>DonchianH，取值为1.0；反之为 -1.0
        self.cross_high = bt.ind.CrossOver(
            self.close(0), self.donchian_high, subplot=False
        )

        # 生成唐奇安通道下轨突破:
        self.cross_low = bt.ind.CrossOver(
            self.close(0), self.donchian_low, subplot=False
        )

        # True Range (TR): True Range is a measure of volatility that takes into account the price range of an
        # asset over a certain period. It considers the following three values: The current high minus the current
        # low. The absolute value of the current high minus the previous close. The absolute value of the current low
        # minus the previous close.
        self.TR = bt.ind.Max(
            (self.high(0) - self.low(0)),  # 当日最高价-当日最低价
            abs(self.high(0) - self.close(-1)),  # abs(当日最高价?前一日收盘价)
            abs(self.low(0) - self.close(-1)),
        )  # abs(当日最低价-前一日收盘价)

        self.ATR = bt.ind.MovingAverageSimple(self.TR, period=self.p.N1, subplot=False)

        # 计算 ATR，直接调用 talib ，使用前需要安装 python3 -m pip install TA-Lib
        # self.ATR = bt.talib.ATR(self.high, self.low, self.close, timeperiod=self.p.N1, subplot=True)

    def next(self):
        if self.order:
            return

        if self.position.size > 0:  # 如果当前持有多单
            # 多单加仓:价格上涨了买入价的0.5的ATR且加仓次数少于等于3次
            if (
                self.datas[0].close > self.last_price + 0.5 * self.ATR[0]
                and self.buy_count <= 4
            ):
                # 计算建仓单位：self.ATR*期货合约乘数300*保证金比例0.1
                self.buy_unit = max((self.broker.getvalue() * 0.01) / self.ATR[0], 1)
                self.buy_unit = int(self.buy_unit)  # 交易单位为手
                # self.sizer.p.stake = self.buy_unit
                self.order = self.buy(size=self.buy_unit)
                self.last_price = self.position.price  # 获取买入价格
                self.buy_count = self.buy_count + 1

            # 多单止损：当价格回落2倍ATR时止损平仓
            elif self.datas[0].close < (self.last_price - 2 * self.ATR[0]):
                print("elif self.datas[0].close < (self.last_price - 2*self.ATR[0]):")
                self.order = self.sell(size=abs(self.position.size))
                self.buy_count = 0

            # 多单止盈：当价格突破10日最低点时止盈离场 平仓
            elif self.cross_low < 0:
                print("self.CrossoverL < 0")
                self.order = self.sell(size=abs(self.position.size))
                self.buy_count = 0

        # 如果当前持有空单
        else:  # 如果没有持仓，等待入场时机
            # 入场: 价格突破上轨线且空仓时，做多
            if self.cross_high > 0 and self.buy_count == 0:
                print("if self.CrossoverH > 0 and self.buy_count == 0:")
                # 计算建仓单位：self.ATR*期货合约乘数300*保证金比例0.1
                self.buy_unit = max((self.broker.getvalue() * 0.01) / self.ATR[0], 1)
                self.buy_unit = int(self.buy_unit)  # 交易单位为手
                self.order = self.buy(size=self.buy_unit)
                self.last_price = self.position.price  # 记录买入价格
                self.buy_count = 1  # 记录本次交易价格
            # 入场: 价格跌破下轨线且空仓时
            elif self.cross_low < 0 and self.buy_count == 0:
                print("self.CrossoverL < 0 and self.buy_count == 0")


class TurtleTrading(BaseStrategy):
    """ """

    params = (
        ("entry_breakout", 20),
        ("exit_breakdown", 10),
        ("unit_risk", 2),
        ("max_units", 5),
        ("stop_loss", 2),
    )

    def __init__(self):
        self.high_20 = bt.ind.Highest(self.high(-1), period=0, subplot=True)
        self.low_10 = bt.ind.Highest(self.low(-1), period=10, subplot=True)
        self.atr = self.data.high - self.data.low
        self.atr_sma = self.data.high.rolling(window=20).apply(np.mean)
        self.stop_loss = None
        self.units = None
        self.entry_price = None
        self.exit_price = None

    def next(self):
        if not self.position:
            if self.data.close[0] > self.high_20[0]:
                self.entry_price = self.data.close[0]
                self.exit_price = self.low_10[0]
                self.units = math.floor(
                    self.params.unit_risk
                    * self.broker.cash
                    / self.params.stop_loss
                    / self.atr_sma[0]
                    * self.data.close[0]
                )
                self.stop_loss = (
                    self.entry_price - self.params.stop_loss * self.atr_sma[0]
                )
                self.buy(size=self.units)
        else:
            if self.data.close[0] < self.exit_price:
                self.exit_price = self.low_10[0]
                self.sell()
            elif (
                self.data.close[0]
                > self.entry_price + self.params.stop_loss * self.atr_sma[0]
            ):
                self.entry_price = self.data.close[0]
                self.exit_price = self.low_10[0]
                self.stop_loss = (
                    self.entry_price - self.params.stop_loss * self.atr_sma[0]
                )
                if self.units < self.params.max_units:
                    self.units += 1
                    self.buy(size=1)
                else:
                    self.stop_loss = (
                        self.data.close[0] - self.params.stop_loss * self.atr_sma[0]
                    )
            if self.data.close[0] < self.stop_loss:
                self.sell()


if __name__ == "__main__":
    engine = AITrader()
    engine.add_strategy(TurtleTradingStrategy)
    engine.run()
    engine.plot()
