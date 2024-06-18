import backtrader as bt

from ai_trader.strategy.base import BaseStrategy
from ai_trader.trader import AITrader


class ROCStochStrategy(BaseStrategy):
    params = (
        ("roc_period", 12),
        ("stoch_period", 14),
        ("stoch_smooth", 3),
        ("oversold", 20),
        ("overbought", 80),
    )

    def __init__(self):
        self.roc = bt.indicators.RateOfChange(
            self.data.close, period=self.params.roc_period
        )
        self.stoch = bt.indicators.Stochastic(
            self.data,
            period=self.params.stoch_period,
            period_dfast=self.params.stoch_smooth,
        )

    def next(self):
        signal_buy = (
                self.roc[0] > 0 and self.stoch.lines.percK[0] < self.params.oversold
        )
        signal_sell = (
                self.roc[0] < 0 and self.stoch.lines.percK[0] > self.params.overbought
        )

        if self.position.size == 0:
            if signal_buy:
                self.buy()

        if self.position.size > 0:
            if signal_sell:
                self.close()


class ROCMAStrategy(BaseStrategy):
    params = (
        ("roc_period", 12),
        ("fast_ma_period", 10),
        ("slow_ma_period", 30),
    )

    def __init__(self):
        self.roc = bt.indicators.RateOfChange(
            self.data.close, period=self.params.roc_period
        )
        self.fast_ma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.fast_ma_period
        )
        self.slow_ma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.slow_ma_period
        )
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)

    def next(self):
        buy_signal = self.roc[0] > 0 and self.crossover[0] > 0
        close_signal = self.roc[0] < 0 or self.crossover[0] < 0

        if self.position.size == 0:
            if buy_signal:
                self.buy()

        if self.position.size > 0:
            if close_signal:
                self.close()


if __name__ == "__main__":
    engine = AITrader()
    engine.add_strategy(ROCMAStrategy)
    engine.run()
    engine.plot()
