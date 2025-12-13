import backtrader as bt

from ai_trader.trader import AITrader
from ai_trader.backtesting.strategies.base import BaseStrategy
from ai_trader.backtesting.strategies.indicators import VCPPattern


class VCPStrategy(BaseStrategy):
    """
    The Volatility Contraction Pattern (VCP) strategy is a trading strategy popularized by the famous trader
    Mark Minervini. It is used to identify stocks that are poised for a significant breakout after a period of
    decreasing volatility and volume contraction. The idea is that stocks often go through periods of consolidation
    where price movements and trading volumes contract, creating a setup for a potential breakout when
    volatility returns.
    """

    params = dict(
        period_short=10,
        period_long=60,
        period_long_discount=0.7,
        highest_close=100,
        mean_vol=20,
        sustain_period=5,
        min_volume_ratio=0.8,
        sma_long=250,
        sma_short=60,
        recent_price_period=20,
    )

    def __init__(self):
        self.vcp = VCPPattern(
            self.data,
            period_short=self.params.period_short,
            period_long=self.params.period_long,
            period_long_discount=self.params.period_long_discount,
            highest_close=self.params.highest_close,
            mean_vol=self.params.mean_vol,
        )
        self.sma_long = bt.indicators.MovingAverageSimple(
            self.data.close, period=self.params.sma_long
        )
        self.sma_short = bt.indicators.MovingAverageSimple(
            self.data.close, period=self.params.sma_short
        )

        recent_close_min = bt.indicators.Lowest(
            self.data.close, period=self.params.recent_price_period
        )
        recent_close_max = bt.indicators.Highest(
            self.data.close, period=self.params.recent_price_period
        )
        self.narrow_channel = recent_close_min > recent_close_max * 0.7

    def next(self):
        # Condition 1: The VCP (Volatility Contraction Pattern) must be positive
        cond_1 = self.vcp > 0

        # Condition 2: The current volume times the current closing price must be greater than 2,000,000
        # This ensures that the classic has sufficient liquidity
        cond_2 = self.data.volume[0] * self.data.close[0] > 2000000

        # Condition 3: The current closing price must be above the 250-day simple moving average (SMA)
        # This indicates that the classic is in an upward trend over the long term
        cond_3 = self.data.close[0] > self.sma_long[0]

        # Condition 4: The classic must be in a narrow price channel
        # This suggests a period of consolidation, which can precede a breakout
        cond_4 = self.narrow_channel > 0

        # Buy signal: All conditions must be met to generate a buy signal
        buy_signal = cond_1 & cond_2 & cond_3 & cond_4

        # Close signal: The current closing price falling below the 60-day simple moving average (SMA)
        # This indicates a potential downtrend, triggering a sell signal
        close_signal = self.data.close[0] < self.sma_short[0]

        if self.position.size == 0:
            if buy_signal:
                self.buy()
        else:
            if close_signal:
                self.close()


if __name__ == "__main__":
    trader = AITrader()
    trader.add_strategy(VCPStrategy)
    trader.run()
    trader.plot()
