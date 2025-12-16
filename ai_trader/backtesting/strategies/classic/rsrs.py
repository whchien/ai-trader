from ai_trader.backtesting.strategies.base import BaseStrategy
from ai_trader.backtesting.strategies.indicators import RSRS


class RSRSStrategy(BaseStrategy):
    """
    https://freewechat.com/a/MzkyODI5ODcyMA==/2247483898/1
    """

    params = dict(period=20, buy_threshold=0.8, close_threshold=0.5)

    def __init__(self):
        self.rsrs = RSRS(self.data, period=self.params.period)

    def next(self):
        buy_signal = self.rsrs.rsrs[0] > self.params.buy_threshold
        close_signal = self.rsrs.rsrs[0] < self.params.close_threshold

        if self.position.size == 0:
            if buy_signal:
                self.buy()
        else:
            if close_signal:
                self.close()


if __name__ == "__main__":
    from ai_trader.utils.backtest import run_backtest

    # Run backtest with RSRSStrategy
    results = run_backtest(
        strategy=RSRSStrategy,
        data_source=None,  # Use example data
        cash=1000000,
        commission=0.001425,
    )

    print("Backtest completed! Use cerebro.plot() to visualize results.")
