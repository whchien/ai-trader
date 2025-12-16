import backtrader as bt

from ai_trader.backtesting.strategies.base import BaseStrategy
from ai_trader.backtesting.strategies.indicators import HybridAlphaRSI


class HybridAlphaRSIStrategy(BaseStrategy):
    """
    Hybrid AlphaRSI Strategy - Most sophisticated approach combining all enhancements.

    This strategy combines:
    1. Adaptive RSI period (responds to volatility and market cycles)
    2. Adaptive overbought/oversold levels (widens/narrows with volatility)
    3. Trend bias filter (only trades aligned with underlying trend)

    Entry Logic (Buy):
    - Adaptive RSI crosses above adaptive oversold level (from below)
    - AND trend bias is positive (uptrend confirmed by SMA slope)

    Exit Logic (Sell):
    - Adaptive RSI crosses below adaptive overbought level (from above)
    - AND trend bias is negative (downtrend confirmed by SMA slope)

    This strategy generates the highest quality signals by requiring alignment
    across multiple adaptive components, making it most suitable for experienced
    traders and sophisticated market conditions.
    """

    params = dict(
        rsi_length=14,
        atr_length=14,
        atr_ma_period=50,
        min_period=8,
        max_period=28,
        adaptive_sensitivity=1.0,
        smoothing_length=3,
        trend_sma_period=50,
        level_sensitivity=20,
        ob_base=70,
        os_base=30,
        ob_min=65,
        ob_max=85,
        os_min=15,
        os_max=35,
    )

    def __init__(self):
        super().__init__()
        # Initialize the Hybrid AlphaRSI indicator with strategy parameters
        self.indicator = HybridAlphaRSI(
            self.data,
            rsi_length=self.p.rsi_length,
            atr_length=self.p.atr_length,
            atr_ma_period=self.p.atr_ma_period,
            min_period=self.p.min_period,
            max_period=self.p.max_period,
            adaptive_sensitivity=self.p.adaptive_sensitivity,
            smoothing_length=self.p.smoothing_length,
            trend_sma_period=self.p.trend_sma_period,
            level_sensitivity=self.p.level_sensitivity,
            ob_base=self.p.ob_base,
            os_base=self.p.os_base,
            ob_min=self.p.ob_min,
            ob_max=self.p.ob_max,
            os_min=self.p.os_min,
            os_max=self.p.os_max,
        )

    def next(self):
        # Extract indicator values
        rsi = self.indicator.rsi[0]
        os_level = self.indicator.os_level[0]
        ob_level = self.indicator.ob_level[0]
        trend_bias = self.indicator.trend_bias[0]

        # Check for crossover signals
        rsi_cross_up = rsi > os_level and self.indicator.rsi[-1] <= self.indicator.os_level[-1]
        rsi_cross_down = rsi < ob_level and self.indicator.rsi[-1] >= self.indicator.ob_level[-1]

        # Strong signals: crossover + trend alignment
        buy_signal = rsi_cross_up and trend_bias > 0
        sell_signal = rsi_cross_down and trend_bias < 0

        # Execute trades
        if self.position.size == 0:
            if buy_signal:
                self.buy()
        else:
            if sell_signal:
                self.close()


if __name__ == "__main__":
    from ai_trader.utils.backtest import run_backtest

    # Run backtest with HybridAlphaRSIStrategy
    results = run_backtest(
        strategy=HybridAlphaRSIStrategy,
        data_source=None,  # Use example data
        cash=1000000,
        commission=0.001425,
    )

    print("Backtest completed! Use cerebro.plot() to visualize results.")
