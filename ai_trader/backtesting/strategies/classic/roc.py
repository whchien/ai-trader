"""
Rate of Change (ROC) Strategies

Implements three strategies using the Rate of Change indicator:
1. ROC + Stochastic: Momentum with oversold/overbought conditions
2. ROC + Moving Average: Momentum with trend confirmation
3. Naive ROC: Simple threshold-based momentum trading
"""

import backtrader as bt

from ai_trader.backtesting.strategies.base import BaseStrategy


class ROCStochStrategy(BaseStrategy):
    """
    ROC + Stochastic Strategy - Momentum with mean reversion confirmation.

    Combines positive momentum (ROC > 0) with oversold conditions (Stoch < 20)
    for entry, and negative momentum with overbought (Stoch > 80) for exit.
    Generates stronger signals by requiring both indicators to align.

    Entry Logic (Buy):
    - Rate of Change > 0 (positive momentum) AND
    - Stochastic %K < 20 (oversold, ready to bounce)

    Exit Logic (Sell):
    - Rate of Change < 0 (negative momentum) AND
    - Stochastic %K > 80 (overbought, vulnerable to pullback)

    Parameters:
    - roc_period (int): Period for ROC calculation [default: 12]
    - stoch_period (int): Period for Stochastic calculation [default: 14]
    - stoch_smooth (int): Smoothing period for Stochastic %K [default: 3]
    - oversold (int): Stochastic level for oversold condition [default: 20]
    - overbought (int): Stochastic level for overbought condition [default: 80]

    Notes:
    - ROC = (Close - Close n periods ago) / Close n periods ago
    - Stochastic values range 0-100; typical levels: <20 oversold, >80 overbought
    - Dual confirmation reduces false signals vs single indicator
    """

    params = dict(roc_period=12, stoch_period=14, stoch_smooth=3, oversold=20, overbought=80)

    def __init__(self):
        """Initialize Rate of Change and Stochastic indicators."""
        self.roc = bt.indicators.RateOfChange(self.data.close, period=self.params.roc_period)
        self.stoch = bt.indicators.Stochastic(
            self.data,
            period=self.params.stoch_period,
            period_dfast=self.params.stoch_smooth,
        )

    def next(self):
        """Execute trading logic: buy on momentum + oversold, sell on negative momentum + overbought."""
        signal_buy = self.roc[0] > 0 and self.stoch.lines.percK[0] < self.params.oversold
        signal_sell = self.roc[0] < 0 and self.stoch.lines.percK[0] > self.params.overbought

        if self.position.size == 0:
            if signal_buy:
                self.buy()

        if self.position.size > 0:
            if signal_sell:
                self.close()


class ROCMAStrategy(BaseStrategy):
    """
    ROC + Moving Average Strategy - Momentum with trend confirmation.

    Requires positive momentum (ROC > 0) AND bullish moving average crossover
    (fast MA > slow MA) for entry. Exits on negative momentum OR bearish crossover.
    More selective than pure momentum, reduces whipsaws in choppy markets.

    Entry Logic (Buy):
    - Rate of Change > 0 (positive momentum) AND
    - Fast MA > Slow MA (bullish trend crossover)

    Exit Logic (Sell):
    - Rate of Change < 0 (momentum loss) OR
    - Fast MA < Slow MA (bearish trend crossover)

    Parameters:
    - roc_period (int): Period for ROC calculation [default: 12]
    - fast_ma_period (int): Period for fast moving average [default: 10]
    - slow_ma_period (int): Period for slow moving average [default: 30]

    Notes:
    - Combined indicators provide confirmation on both momentum and trend
    - Entry requires both conditions; exit on either condition
    - MA crossover acts as trend filter to avoid counter-trend trades
    """

    params = dict(roc_period=12, fast_ma_period=10, slow_ma_period=30)

    def __init__(self):
        """Initialize Rate of Change and moving average crossover indicators."""
        self.roc = bt.indicators.RateOfChange(self.data.close, period=self.params.roc_period)
        self.fast_ma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.fast_ma_period
        )
        self.slow_ma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.slow_ma_period
        )
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)

    def next(self):
        """Execute trading logic: buy on momentum + bullish MA cross, sell on momentum loss or bearish cross."""
        buy_signal = self.roc[0] > 0 and self.crossover[0] > 0
        close_signal = self.roc[0] < 0 or self.crossover[0] < 0

        if self.position.size == 0:
            if buy_signal:
                self.buy()

        if self.position.size > 0:
            if close_signal:
                self.close()


class NaiveROCStrategy(BaseStrategy):
    """
    ROC = [(Current Close – Close n periods ago) / (Close n periods ago)]
    ROC is a momentum oscillator; other indicator types similar to ROC include MACD, RSI and ADX,
    https://www.avatrade.com/education/technical-analysis-indicators-strategies/roc-indicator-strategies

    """

    params = dict(period=20, threshold=0.08)

    def __init__(self):
        self.roc = bt.ind.RateOfChange(self.data, period=self.params.period)
        self.buy_signal = self.roc > self.params.threshold
        self.close_signal = self.roc < -self.params.threshold

    def next(self):
        if self.position.size == 0:
            if self.buy_signal[0]:
                self.buy()

        if self.position.size > 0:
            if self.close_signal[0]:
                self.close()


if __name__ == "__main__":
    from ai_trader.utils.backtest import run_backtest

    # Run backtest with NaiveROCStrategy
    results = run_backtest(
        strategy=NaiveROCStrategy,
        data_source=None,  # Use example data
        cash=1000000,
        commission=0.001425,
    )

    print("Backtest completed! Use cerebro.plot() to visualize results.")
