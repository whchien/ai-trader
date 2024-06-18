import backtrader as bt

from ai_trader.trader import AITrader
from ai_trader.strategy.base import BaseStrategy
from ai_trader.strategy.indicators import (
    AverageVolatility,
    NewHighIn5Days,
    DiffHighLow,
)
from ai_trader.utils import check_rules


class PussycatStrategy(BaseStrategy):
    params = dict(volatility_period=20)

    def __init__(self):
        self.candle_volatility = AverageVolatility(
            self.data, period=self.params.volatility_period
        )
        self.has_new_high = NewHighIn5Days(self.data)
        self.past_5_vol = bt.indicators.MovingAverageSimple(self.data.volume, period=5)
        self.diff_high_low = DiffHighLow(self.data)

    def next(self):
        # k線波動率濾網
        cond_1 = self.candle_volatility.avg_volatility[0] < 8

        # 收盤價近5日至少有1日創收盤價近100日創新
        cond_2 = self.has_new_high.new_high[0] > 0

        # 5日均大於100張
        cond_3 = self.past_5_vol[0] > 100 * 1000

        # 近60日股價高低區間在30%內
        cond_4 = self.diff_high_low.diff[0] < 0.3

        buy_signal = cond_1 & cond_2 & cond_3 & cond_4
        close_signal = check_rules([cond_1, cond_2, cond_3, cond_4], 2)

        if self.position:
            if close_signal:
                self.close()

        else:
            if buy_signal:
                self.buy()


if __name__ == "__main__":
    e = AITrader()
    e.cerebro.addstrategy(PussycatStrategy)
    e.run()
    e.cerebro.plot(iplot=False)
