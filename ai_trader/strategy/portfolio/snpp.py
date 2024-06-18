"""
https://medium.com/@mikelhsia/how-2-upgrade-your-backtesting-arsenal-trading-multiple-stocks-with-backtrader-54368bf36693
"""

import datetime
import os

from ai_trader.strategy.base import BaseStrategy

PATH = os.path.expanduser(f"{os.path.dirname(__file__)}/")
BENCHMARK_SYMBOL = "spy"
SNP_SCAFFOLDING = get_snp_stock_scaffolding(
    "2017-1-1",
    (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
)
HOLDING_MAXIMUM = 15
LOOKBACK_PERIOD = 60


class SNPPreimumStrategy(BaseStrategy):
    params = (("max_holdings", HOLDING_MAXIMUM),)

    def __init__(self):
        self.log_pnl = list()
        self.available_cash = 0
        self.num_of_holdings = 0
        self.buy_list = list()
        self.log_file_handler = open(
            os.path.join(
                PATH, "logs", f'{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.log'
            ),
            "w",
        )
        self.universe = []

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f"{self.datas[0].datetime.date(0).isoformat()}, {txt}")
        self.log_file_handler.write(
            f"{self.datas[0].datetime.date(0).isoformat()}, {txt}\n"
        )

    def start(self):
        """_summary_
        The world (cerebro) tells the strategy is time to start kicking. A default empty method exists.
        """
        print(f"\n\n")

    def next(self):
        """_summary_
        Update tradable universe
        """
        self.universe = get_universe_by_date(self.data.datetime.date(), SNP_SCAFFOLDING)

    def next_open(self):
        """_summary_
        Tiggered before the market open. It's a cheating function when you enable the "cheat_on_open" feature
        Reference: https://www.backtrader.com/docu/cerebro/cheat-on-open/cheat-on-open/
        """
        self.available_cash = self.broker.get_cash()

        # This step is to release those positions that its ticker is delisted
        delisted_orders = dict()
        for i, data in enumerate(self.datas):
            pos = self.getposition(data).size
            if pos != 0 and data.volume[0] == 0:
                delisted_orders[data._name] = self.close(data=data, price=data.open[0])
                self.log(
                    f"[{data._name}] CLOSE CREATED DUE TO DELISTING EVENT {data.open[0]:.2f} {data.open[-1]:.2f}"
                )
                self.available_cash += -delisted_orders[data._name].size * data.open[0]

        """
        Here to input your algorithm to produce buy_list, which is a list of symbols that have high IC or IR ranking. 
        Also, this is where you utilize the hot .data loaded.
        """

        if not self.buy_list:
            return

        # Calculate the number of current holding positions
        self.num_of_holdings = 0
        for i, data in enumerate(self.datas):
            if self.getposition(data).size != 0:
                self.num_of_holdings += 1

        # Close the positions to release available cash
        for i, data in enumerate(self.datas):
            pos = self.getposition(data).size
            if data._name not in self.buy_list and data._name not in delisted_orders:
                if pos != 0:
                    order = self.close(data=data)
                    self.log(f"[{data._name}] CLOSE CREATE {data.open[0]:2f}")
                    self.num_of_holdings -= 1
                    self.available_cash += -order.size * data.open[0]
                else:
                    pass

        if self.num_of_holdings >= self.params.max_holdings:
            return

        # Calculate the amount of capital to allocate to each indiv. Here we're using even-weighting method
        amount_to_allocate = self.available_cash / (
            self.params.max_holdings - self.num_of_holdings
        )

        # Open new positions
        for i, data in enumerate(self.datas):
            pos = self.getposition(data).size
            if data._name in self.buy_list and data._name not in delisted_orders:
                if pos == 0 and data.open[0] != 0:
                    order = self.buy(
                        data=data, size=int(amount_to_allocate / data.open[0])
                    )
                    self.log(f"[{data._name}] BUY CREATE {data.open[0]:2f}")
                    self.num_of_holdings += 1
                    self.available_cash -= order.size * data.open[0]
                else:
                    self.log(f"[{data._name}] BUY EXISTED")

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # An active Buy/Sell order has been submitted/accepted
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f"[{order.data._name}] BUY EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Size: {order.executed.size}, PnL: {order.executed.pnl}, pprice: {order.executed.pprice}"
                )
            elif order.issell():
                self.log(
                    f"[{order.data._name}] SELL EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Size: {order.executed.size}, PnL: {order.executed.pnl}, pprice: {order.executed.pprice}"
                )
            if round(self.available_cash, 2) != round(self.broker.get_cash(), 2):
                raise ValueError(
                    f"Something wrong with the available cash calculation ({round(self.available_cash, 2)} / {round(self.broker.get_cash(), 2)})"
                )

        elif order.status in [
            order.Canceled,
            order.Margin,
            order.Rejected,
            order.Partial,
        ]:
            if order.status == order.Canceled:
                status = "Canceled"
            elif order.status == order.Margin:
                status = "Margin"
            elif order.status == order.Partial:
                status = "Partial"
            else:
                status = "Rejected"
            self.log(f"[{order.data._name}] Order place failed - status: {status}")
            self.available_cash += order.price * order.size

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

    def notify_store(self, msg, *args, **kwargs):
        self.log(f"***** STORE NOTIF: {msg}")

    def stop(self):
        """_summary_
        To put additional log here
        """
        self.log_file_handler.close()
