import backtrader as bt

from ai_trader.trader import AITrader
from ai_trader.strategy.base import BaseStrategy
from ai_trader.strategy.indicators import (
    AverageVolatility,
    RecentHigh,
    DiffHighLow,
)


class RiskAverseStrategy(BaseStrategy):
    """
    The strategy is designed to buy stocks that exhibit low volatility, have recently made new highs,
    have high trading volume, and show a small difference between their high and low prices over a specified period.
    The strategy exits positions if multiple conditions indicate that the favorable conditions no longer hold. This
    strategy aims to capitalize on stocks that are stable, have upward momentum, and are actively traded.
    """

    params = dict(
        volatility_period=20,
        high_low_period=60,
        vol_period=5,
        volatility_threshold=8,
        high_low_threshold=0.3,
    )

    def __init__(self):
        self.candle_volatility = AverageVolatility(
            self.data, period=self.params.volatility_period
        )
        self.has_new_high = RecentHigh(self.data)
        self.past_vol = bt.indicators.SimpleMovingAverage(
            self.data.volume, period=self.params.vol_period
        )
        self.diff_high_low = DiffHighLow(self.data, period=self.params.high_low_period)

    def next(self):
        # Conditions
        cond_1 = (
            self.candle_volatility.avg_volatility[0] < self.params.volatility_threshold
        )
        cond_2 = self.has_new_high.new_high[0] > 0
        cond_3 = self.past_vol[0] > 100 * 1000
        cond_4 = self.diff_high_low.diff[0] < self.params.high_low_threshold

        # Combined signals
        conditions = [cond_1, cond_2, cond_3, cond_4]
        buy_signal = all(conditions)
        close_signal = sum(not cond for cond in conditions) >= 2

        # Execute trades based on signals
        if self.position:
            if close_signal:
                self.close()
        elif buy_signal:
            self.buy()


if __name__ == "__main__":
    trader = AITrader()
    trader.add_strategy(RiskAverseStrategy)
    trader.run()
    trader.plot()
