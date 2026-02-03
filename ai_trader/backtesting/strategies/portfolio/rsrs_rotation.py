from ai_trader.backtesting.strategies.base import BaseStrategy
from ai_trader.backtesting.strategies.indicators import RSRS


class RSRSRotationStrategy(BaseStrategy):
    """
    RSRS Rotation Strategy - Multi-asset portfolio rotation using trend strength.

    Dynamically rotates capital to assets with the strongest uptrend confirmation
    (RSRS > 1.0) and exits from assets with weakening trends (RSRS < 0.8).
    Equal-weight allocation among selected assets. RSRS measures the slopes of
    support and resistance lines to quantify trend strength and reliability.

    Entry Logic (Buy):
    - Asset RSRS > 1.0 (very strong uptrend confirmed)
    - Asset selected for portfolio inclusion

    Exit Logic (Sell):
    - Asset RSRS < 0.8 (trend strength deteriorating)
    - Position closed to reduce exposure to weakening trends

    Parameters:
    - period (int): Period for RSRS calculation [default: 20]

    References:
    - https://freewechat.com/a/MzkyODI5ODcyMA==/2247483898/1
    - https://mp.weixin.qq.com/s?__biz=MzIwNTU2ODMwNg==&mid=2247486024&idx=1&sn=e1dc5baa2894a15cfafe959d925f3ec1&chksm=972faa15a058230357dbd0dd9a4b700eff74f14e2d92494eb3b4f5b85d5c0a4bb77dfb1ab268&scene=21#wechat_redirect

    Notes:
    - RSRS > 1.0 indicates very strong uptrend with steep resistance
    - RSRS < 0.8 indicates trend weakening or reversing
    - Equal-weight allocation provides diversification across selected assets
    - No top-k limit; all assets meeting buy criteria are included
    """

    params = dict(
        period=20,  # Momentum period
    )

    def __init__(self):
        """Initialize RSRS indicators for all assets in the portfolio."""
        # Indicator calculations
        self.inds = {data: RSRS(data, period=self.params.period) for data in self.datas}

    def next(self):
        """Execute portfolio rebalancing: exit weak trends, rotate to strong uptrends."""
        to_buy, to_sell, holding = [], [], []

        for data, rsrs in self.inds.items():
            buy_signal = rsrs[0] > 1
            close_signal = rsrs[0] < 0.8

            if buy_signal:
                to_buy.append(data)
            if close_signal:
                to_sell.append(data)

            if self.getposition(data).size > 0:
                holding.append(data)

        # Close positions for data in to_sell list
        for sell in to_sell:
            if self.getposition(sell).size > 0:
                self.close(sell)

        # Update the list of holdings
        new_hold = list(set(to_buy + holding))
        for data in to_sell:
            if data in new_hold:
                new_hold.remove(data)

        if not new_hold:
            # New holdings list is empty
            return

        # Equal weight allocation
        # Existing positions should remain unchanged; cash should be equally allocated among new additions
        weight = 1 / len(new_hold)
        for data in new_hold:
            self.order_target_percent(data, weight)


if __name__ == "__main__":
    from ai_trader.utils.backtest import run_backtest

    # Run backtest with RSRSRotationStrategy
    results = run_backtest(
        strategy=RSRSRotationStrategy,
        data_source=None,  # Use example data
        cash=1000000,
        commission=0.001425,
    )

    print("Backtest completed! Use cerebro.plot() to visualize results.")
