from ai_trader.backtesting.strategies.base import BaseStrategy


class BuyHoldStrategy(BaseStrategy):
    def next(self):
        if self.position.size == 0:
            self.buy()


if __name__ == "__main__":
    from ai_trader.utils.backtest import run_backtest

    # Run backtest with BuyHoldStrategy
    results = run_backtest(
        strategy=BuyHoldStrategy,
        data_source=None,  # Use example data
        cash=1000000,
        commission=0.001425,
    )

    print("Backtest completed! Use cerebro.plot() to visualize results.")
