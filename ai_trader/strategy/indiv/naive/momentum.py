import backtrader as bt

from ai_trader.trader import AITrader
from ai_trader.strategy.base import BaseStrategy


class MTMStrategy(BaseStrategy):
    """
    https://en.wikipedia.org/wiki/Momentum_(technical_analysis)
    """

    params = (
        ("sma_period", 50),
        ("momentum_period", 14),
    )

    def __init__(self):
        self.sma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.sma_period
        )
        self.momentum = bt.indicators.Momentum(
            self.data.close, period=self.params.momentum_period
        )
        self.buy_signal = self.momentum > 0
        self.close_signal = self.data.close < self.sma

    def next(self):
        if self.position.size == 0:
            if self.buy_signal[0]:
                self.buy()
        else:
            if self.close_signal[0]:
                self.close()


class NaiveROCStrategy(BaseStrategy):
    """
    ROC = [(Current Close – Close n periods ago) / (Close n periods ago)]

    ROC is a momentum oscillator; other indicator types similar to ROC include MACD, RSI and ADX,

    https://www.avatrade.com/education/technical-analysis-indicators-strategies/roc-indicator-strategies

    """

    params = (("period", 20), "threshold", 0.08)

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
    engine = AITrader()
    engine.add_strategy(MTMStrategy)
    engine.run()
    engine.plot()
