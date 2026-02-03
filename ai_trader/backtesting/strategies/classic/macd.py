import backtrader as bt

from ai_trader.backtesting.strategies.base import BaseStrategy


class MACDStrategy(BaseStrategy):
    """
    MACD Strategy - Trend-following via moving average crossovers and histogram.

    MACD consists of three components:
    - DIF (MACD line): Fast EMA (12-day) - Slow EMA (26-day); measures momentum
    - DEA (Signal line): EMA of the DIF line; acts as trigger for crossovers
    - MACD Histogram: DIF - DEA; visually shows momentum strength and divergence

    Entry Logic (Buy):
    - Golden cross: DIF crosses above DEA (bullish crossover)
    - AND both DIF and DEA are above zero (uptrend context)

    Exit Logic (Sell):
    - Death cross: DIF crosses below DEA (bearish crossover)
    - No histogram confirmation needed for exit (captures reversals quickly)

    Parameters:
    - fastperiod (int): Fast EMA period [default: 12]
    - slowperiod (int): Slow EMA period [default: 22]
    - signalperiod (int): Signal line (DEA) EMA period [default: 8]

    Notes:
    - Golden cross indicates momentum shift from negative to positive
    - Death cross indicates reversal from positive to negative momentum
    - Positive histogram confirmation on buy reduces false signals
    - MACD works well on daily and longer timeframes
    - Relatively slow indicator; lags on fast intraday moves
    """

    params = dict(fastperiod=12, slowperiod=22, signalperiod=8)

    def __init__(self):
        """Initialize MACD with crossover detection and positive histogram confirmation."""
        kwargs = {
            "fastperiod": self.p.fastperiod,
            "fastmatype": bt.talib.MA_Type.EMA,
            "slowperiod": self.p.slowperiod,
            "slowmatype": bt.talib.MA_Type.EMA,
            "signalperiod": self.p.signalperiod,
            "signalmatype": bt.talib.MA_Type.EMA,
        }

        self.macd = bt.talib.MACDEXT(self.data0.close, **kwargs)
        self.crossover = bt.indicators.CrossOver(self.macd.macd, self.macd.macdsignal, plot=False)
        self.above = bt.And(self.macd.macd > 0.0, self.macd.macdsignal > 0.0)
        self.buy_signal = bt.And(self.above, self.crossover == 1)
        self.sell_signal = self.crossover == -1

        self.order = None

    def next(self):
        """Execute trading logic: buy on golden cross with positive histogram, sell on death cross."""
        if self.order:
            return

        if not self.position:
            if self.buy_signal[0]:
                self.buy()
        else:
            if self.sell_signal[0]:
                self.sell()


if __name__ == "__main__":
    from ai_trader.utils.backtest import run_backtest

    # Run backtest with MACDStrategy
    results = run_backtest(
        strategy=MACDStrategy,
        data_source=None,  # Use example data
        cash=1000000,
        commission=0.001425,
    )

    print("Backtest completed! Use cerebro.plot() to visualize results.")
