import backtrader as bt

from ai_trader.backtesting.strategies.base import BaseStrategy
from ai_trader.backtesting.strategies.indicators import AdaptiveRSI


class AdaptiveRSIStrategy(BaseStrategy):
    """
    Adaptive RSI Strategy - Uses dynamic RSI period based on market conditions.

    Entry Logic (Buy):
    - RSI crosses above oversold level (30) from below
    - OR extreme bullish reversal: RSI < 20 and shows reversal pattern

    Exit Logic (Sell):
    - RSI crosses below overbought level (70) from above
    - OR extreme bearish reversal: RSI > 80 and shows reversal pattern

    The RSI period adapts to market volatility and cycles:
    - High volatility/fast cycles → shorter period (more responsive)
    - Low volatility/slow cycles → longer period (more stable)
    """

    params = dict(
        rsi_length=14,
        atr_length=14,
        min_period=8,
        max_period=28,
        adaptive_sensitivity=1.0,
        smoothing_length=3,
        ob_level=70,
        os_level=30,
        extreme_ob_level=80,
        extreme_os_level=20,
    )

    def __init__(self):
        super().__init__()
        # Initialize the Adaptive RSI indicator with strategy parameters
        self.indicator = AdaptiveRSI(
            self.data,
            rsi_length=self.p.rsi_length,
            atr_length=self.p.atr_length,
            min_period=self.p.min_period,
            max_period=self.p.max_period,
            adaptive_sensitivity=self.p.adaptive_sensitivity,
            smoothing_length=self.p.smoothing_length,
            ob_level=self.p.ob_level,
            os_level=self.p.os_level,
            extreme_ob_level=self.p.extreme_ob_level,
            extreme_os_level=self.p.extreme_os_level,
        )

    def next(self):
        # Extract indicator values
        rsi = self.indicator.rsi[0]

        # Primary signals: crossover of standard levels
        buy_signal_os = rsi >= self.p.os_level and self.indicator.rsi[-1] < self.p.os_level
        sell_signal_ob = rsi <= self.p.ob_level and self.indicator.rsi[-1] > self.p.ob_level

        # Extreme reversal signals
        extreme_bull_reversal = (
            rsi < self.p.extreme_os_level
            and rsi > self.indicator.rsi[-1]
            and self.indicator.rsi[-1] < self.indicator.rsi[-2]
        )
        extreme_bear_reversal = (
            rsi > self.p.extreme_ob_level
            and rsi < self.indicator.rsi[-1]
            and self.indicator.rsi[-1] > self.indicator.rsi[-2]
        )

        # Combine signals
        buy_signal = buy_signal_os or extreme_bull_reversal
        sell_signal = sell_signal_ob or extreme_bear_reversal

        # Execute trades
        if self.position.size == 0:
            if buy_signal:
                self.buy()
        else:
            if sell_signal:
                self.close()


if __name__ == "__main__":
    from ai_trader.utils.backtest import run_backtest

    # Run backtest with AdaptiveRSIStrategy
    results = run_backtest(
        strategy=AdaptiveRSIStrategy,
        data_source=None,  # Use example data
        cash=1000000,
        commission=0.001425,
    )

    print("Backtest completed! Use cerebro.plot() to visualize results.")
