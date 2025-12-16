import backtrader as bt

from ai_trader.backtesting.strategies.base import BaseStrategy


class BBandsStrategy(BaseStrategy):
    params = dict(period=20, devfactor=2)

    def __init__(self):
        self.bb = bt.indicators.BollingerBands(
            self.data, period=self.params.period, devfactor=self.params.devfactor
        )

    def next(self):
        signal_buy = self.data.close[0] < self.bb.lines.bot[0]
        signal_sell = self.data.close[0] > self.bb.lines.top[0]

        if self.position.size == 0:
            if signal_buy:
                self.buy()

        if self.position.size > 0:
            if signal_sell:
                self.close()


if __name__ == "__main__":
    from ai_trader.utils.backtest import run_backtest

    # Run backtest with Bollinger Bands strategy
    results = run_backtest(
        strategy=BBandsStrategy,
        data_source=None,  # Use example data
        cash=1000000,
        commission=0.001425,
        strategy_params={"period": 20, "devfactor": 2.0},
    )

    print("\nBacktest completed! Use cerebro.plot() to visualize results.")
