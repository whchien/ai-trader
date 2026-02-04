"""
Rate of Change (ROC) Rotation Strategy

Multi-asset portfolio strategy that rotates capital to assets with
the strongest positive momentum, concentrating positions in top-k assets.
"""

import backtrader as bt

from ai_trader.backtesting.strategies.base import BaseStrategy


class ROCRotationStrategy(BaseStrategy):
    """
    ROC Rotation Strategy - Dynamic momentum-based multi-asset rotation.

    A portfolio strategy that applies Rate of Change analysis to multiple assets
    and rotates capital to the top-k assets with strongest momentum (highest ROC).
    Exits positions in assets with negative momentum. Equal-weight allocates
    portfolio among selected assets.

    Entry Logic (Buy):
    - Asset ROC > 0 (positive momentum)
    - Asset ranked in top-k by ROC value (highest momentum)

    Exit Logic (Sell):
    - Asset ROC < 0 (momentum reversal)
    - Position closed and capital reallocated to better opportunities

    Parameters:
    - period (int): Period for ROC calculation [default: 20]
    - top_k (int): Number of top assets to hold (internal, hard-coded to 5)

    Notes:
    - Rotates portfolio monthly or whenever momentum leaders change
    - Concentrates in top-5 assets to optimize risk-adjusted returns
    - Equal-weight allocation across selected assets (95% of capital, 5% buffer)
    - Positive momentum indicates accelerating price movements
    - ROC > 0 shows gains over the past period; < 0 shows losses
    """

    params = dict(period=20)

    def __init__(self):
        """Initialize Rate of Change indicators for all assets in the portfolio."""
        self.indicators = {
            data: bt.ind.RateOfChange(data, period=self.params.period) for data in self.datas
        }

        self.top_k = 5

    def next(self):
        """Execute portfolio rebalancing: exit negative momentum, rotate to top-k momentum leaders."""
        # 1. Select by signals
        # Prepare a quick lookup list of stocks currently holding a position
        holding = [d for d, pos in self.getpositions().items() if pos]
        to_buy = [data for data, roc in self.indicators.items() if roc[0] > 0.0]
        to_close = [data for data, roc in self.indicators.items() if roc[0] < 0.0]

        for data in to_close:
            if data in holding:
                self.order_target_percent(data=data, target=0.0)
                self.log(f"Leave {data._name}")
                holding.remove(data)

        portfolio = list(set(to_buy + holding))

        if not portfolio:  # If no stocks are selected, return
            return

        # 2. Select top k
        if len(portfolio) > self.top_k:
            data_roc = {item: self.indicators[item][0] for item in portfolio}
            portfolio = sorted(
                data_roc.items(),  # Get the (data, roc) pair
                key=lambda x: x[1],
                reverse=True,  # Highest ranked first
            )
            portfolio = [item[0] for item in portfolio[: self.top_k]]
            self.log(f"Selected portfolio: {[p._name for p in portfolio]}")

        # 3. Equal weight allocation
        # Existing positions remain unchanged, cash is equally allocated among new additions
        weight = 1 / len(portfolio)
        for p in portfolio:
            if p in holding:
                self.log(f"Rebalance {p._name}")
                self.order_target_percent(p, target=weight * 0.95)
            else:
                self.log(f"Enter {p._name}")
                self.order_target_percent(p, target=weight * 0.95)


if __name__ == "__main__":
    from ai_trader.utils.backtest import run_backtest

    # Run backtest with ROCRotationStrategy
    results = run_backtest(
        strategy=ROCRotationStrategy,
        data_source=None,  # Use example data
        cash=1000000,
        commission=0.001425,
    )

    print("Backtest completed! Use cerebro.plot() to visualize results.")
