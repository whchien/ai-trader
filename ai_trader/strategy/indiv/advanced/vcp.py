import backtrader as bt

from ai_trader.trader import AITrader
from ai_trader.strategy.base import BaseStrategy
from ai_trader.strategy.indicators import VolatilityContractionPattern


class VolatilityContractionStrategy(BaseStrategy):
    """
    The Volatility Contraction Pattern (VCP) strategy is a trading strategy popularized by the famous trader
    Mark Minervini. It is used to identify stocks that are poised for a significant breakout after a period of
    decreasing volatility and volume contraction. The idea is that stocks often go through periods of consolidation
    where price movements and trading volumes contract, creating a setup for a potential breakout when
    volatility returns.

    Key Concepts of Volatility Contraction Strategy (VCP)
    Volatility Contraction: Stocks exhibit a pattern where the price volatility decreases over time. This means that the
    trading range (the difference between the high and low prices) becomes narrower. The pattern usually consists of
    several waves of contraction, where each wave has a lower high and higher low compared to the previous wave.

    Volume Contraction: Alongside price contraction, there is a decrease in trading volume. This suggests that fewer
    traders are participating, which can precede a significant move when volume returns. A significant increase in
    volume during the breakout confirms the strength of the move.

    Breakout: After a period of contraction, the indiv breaks out above a resistance level on increased volume.
    This breakout is the signal for traders to enter a position, anticipating a continued upward move.
    """

    params = (
        ("rsi_short", 20),
        ("rsi_mid", 60),
        ("rsi_long", 120),
        ("holding_period", 60),
    )

    def __init__(self):
        self.vcp = VolatilityContractionPattern(self.data)
        self.sma_250 = bt.indicators.MovingAverageSimple(self.data.close, period=250)
        self.sma_60 = bt.indicators.MovingAverageSimple(self.data.close, period=60)

        close_min_20 = bt.indicators.Lowest(self.data.close, period=20)
        close_max_20 = bt.indicators.Highest(self.data.close, period=20)
        self.narrow_channel = close_min_20 > close_max_20 * 0.7

    def next(self):
        # Condition 1: The VCP (Volatility Contraction Pattern) must be positive
        cond_1 = self.vcp > 0

        # Condition 2: The current volume times the current closing price must be greater than 2,000,000
        # This ensures that the indiv has sufficient liquidity
        cond_2 = self.data.volume[0] * self.data.close[0] > 2000000

        # Condition 3: The current closing price must be above the 250-day simple moving average (SMA)
        # This indicates that the indiv is in an upward trend over the long term
        cond_3 = self.data.close[0] > self.sma_250[0]

        # Condition 4: The indiv must be in a narrow price channel
        # This suggests a period of consolidation, which can precede a breakout
        cond_4 = self.narrow_channel > 0

        # Buy signal: All conditions must be met to generate a buy signal
        buy_signal = cond_1 & cond_2 & cond_3 & cond_4

        # Close signal: The current closing price falling below the 60-day simple moving average (SMA)
        # This indicates a potential downtrend, triggering a sell signal
        close_signal = self.data.close[0] < self.sma_60[0]

        if self.position.size == 0:
            if buy_signal:
                self.buy()
        else:
            if close_signal:
                self.close()


if __name__ == "__main__":
    engine = AITrader()
    engine.add_strategy(VolatilityContractionStrategy)
    engine.run()
    engine.plot()
