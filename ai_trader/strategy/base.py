import backtrader as bt


class BaseStrategy(bt.Strategy):
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print("%s, %s" % (dt.isoformat(), txt))

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f"[BUY] Price: {round(order.executed.price,2):<10}"
                    f"| Cost: {round(order.executed.value):<10}"
                    f"| Comm: {round(order.executed.comm)}"
                )
            elif order.issell():
                self.log(
                    f"[SELL] Price: {round(order.executed.price, 2):<10}"
                    f"| Cost: {round(order.executed.value):<10}"
                    f"| Comm: {round(order.executed.comm)}"
                )

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            if order.status == order.Canceled:
                status = "Canceled"
            elif order.status == order.Margin:
                status = "Margin"
            elif order.status == order.Partial:
                status = "Partial"
            else:
                status = "Rejected"
            self.log(f"[{order.data._name}] Order place failed - status: {status}")
            # self.available_cash += order.price * order.size

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log(
            f"[OPERATION PROFIT]"
            f"Gross: {round(trade.pnl):<10}| "
            f"Net: {round(trade.pnlcomm)}"
        )
