import backtrader as bt

from ai_trader.backtesting.strategies.base import BaseStrategy
from ai_trader.backtesting.strategies.indicators import TripleRSI

import backtrader as bt


class TripleRSIRotationStrategy(BaseStrategy):
    """
    The main entry condition for this strategy is the strengthening of the long-term RSI indicator.
    The primary entry condition is when the stock price falls below the quarterly moving average,
    and the short-term RSI is not overheated. When the medium to long-term RSI performs stably,
    it is suitable for holding. Stocks are rotated monthly.

    More details: https://zhuanlan.zhihu.com/p/269443883
    """

    params = dict(
        rebal_month=[2, 4, 6, 8, 10, 12],  # Re-balancing months
        rebal_monthday=[5],  # Re-balancing day of the month
        num_volume=5,  # Number of top volume stocks to select
        rsi_short=20,
        rsi_mid=60,
        rsi_long=120,
        holding_period=60,
        oversold=55,
        overbought=75,
    )

    def __init__(self):
        self.indicators = {
            data: TripleRSI(
                data,
                rsi_short=self.params.rsi_short,
                rsi_mid=self.params.rsi_mid,
                rsi_long=self.params.rsi_long,
                oversold=self.params.oversold,
                overbought=self.params.overbought,
            )
            for data in self.datas
        }
        self.order_list = []
        self.last_buy = []

        # Schedule a timer to invoke notify_timer
        self.add_timer(
            when=bt.Timer.SESSION_START,
            monthdays=self.params.rebal_monthday,  # Trigger rebalancing on specified day
            monthcarry=True,  # Carry over if rebalancing day is not a trading day
        )

    def notify_timer(self, timer, when, *args, **kwargs):
        self.rebalance()

    def next(self):
        pass

    def rebalance(self):
        # Get current date from index
        current_date = self.data0.datetime.date(0)
        self.log(f"Rebalance date: {current_date}")

        # Exit if it's the last bar to prevent out-of-bounds error
        if len(self.datas[0]) == self.data0.buflen():
            return

        # Cancel previous orders (won't affect filled orders)
        for o in self.order_list:
            self.cancel(o)
        self.order_list = []  # Reset order list

        # 1. Exclusion filtering process
        to_buy = [data for data, rsi in self.indicators.items() if rsi.signal[0] > 0]

        if not to_buy:  # No stocks selected, return
            self.log("No target stocks found...")
            return

        # 2. Sorting and selection process
        to_buy.sort(key=lambda d: d.volume, reverse=True)  # Sort by volume (descending)
        to_buy = to_buy[: self.params.num_volume]  # Select top num_volume stocks

        # 3. Close positions not in the new selection
        to_close = set(self.last_buy) - set(to_buy)
        for data in to_close:
            self.log(f"Leave: {data._name} | Size: {self.getposition(data).size}")
            o = self.close(data=data)
            self.order_list.append(o)  # Record order

        # 4. Order for new selection
        # Allocate 98% of cash equally among the selected stocks
        weight = (1 - 0.02) / len(to_buy)

        # Sort stocks by current holding value (descending) to ensure sell before buy
        to_buy.sort(key=lambda d: self.broker.getvalue([d]), reverse=True)
        self.log(
            f"Order - target_number: {len(to_buy)} | "
            f"target_value: {weight * self.broker.getvalue()} | "
            f"current_ttl_value: {self.broker.getvalue()}"
        )

        for data in to_buy:
            if data in self.last_buy:
                self.log(f"Rebalance {data._name}")
            else:
                self.log(f"Enter {data._name}")

            o = self.order_target_percent(data, target=weight * 0.95)
            self.order_list.append(o)

        self.last_buy = to_buy  # Track last bought stocks


if __main__ == "__main__":
    from ai_trader.utils.backtest import run_backtest

    # Run backtest with TripleRSIRotationStrategy
    results = run_backtest(
        strategy=TripleRSIRotationStrategy,
        data_source=None,  # Use example data
        cash=1000000,
        commission=0.001425,
    )

    print("
Backtest completed! Use cerebro.plot() to visualize results.")
