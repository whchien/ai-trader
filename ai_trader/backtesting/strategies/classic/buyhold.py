"""
Buy and Hold Strategy

A passive benchmark strategy that buys and holds an asset without active trading.
Used as a baseline to compare the performance of active trading strategies.
"""

from ai_trader.backtesting.strategies.base import BaseStrategy


class BuyHoldStrategy(BaseStrategy):
    """
    Buy and Hold Strategy - Passive long-only benchmark strategy.

    This is the simplest possible trading strategy, serving as a baseline benchmark
    for comparing active trading strategy performance. It buys the asset on the first
    bar and holds until the end of the backtest period without selling.

    Entry Logic (Buy):
    - Buy on the first bar when position size is zero (one-time entry)

    Exit Logic (Sell):
    - Never sells; position held indefinitely

    Notes:
    - Used as a benchmark to validate that active strategies add value
    - Captures market appreciation without timing risk
    - Transaction costs (commissions) reduce returns compared to pure buy-and-hold
    """

    def __init__(self):
        """Initialize Buy and Hold strategy (no indicators needed)."""
        pass

    def next(self):
        """Execute buy-and-hold logic: buy once and never sell."""
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
