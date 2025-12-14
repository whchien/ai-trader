import backtrader as bt

from ai_trader.backtesting.strategies.base import BaseStrategy


class ROCRotationStrategy(BaseStrategy):
    params = dict(period=20)

    def __init__(self):
        self.indicators = {
            data: bt.ind.RateOfChange(data, period=self.params.period)
            for data in self.datas
        }

        self.top_k = 5

    def next(self):
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
