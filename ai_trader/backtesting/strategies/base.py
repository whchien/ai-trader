import backtrader as bt


import backtrader as bt


class BaseStrategy(bt.Strategy):
    def log(self, txt, dt=None):
        """
        Log the provided text with a timestamp.
        """
        dt = dt or self.datas[0].datetime.date(0)
        print(f"{dt.isoformat()}, {txt}")

    def notify_order(self, order):
        """
        Handle order notifications.
        """
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        if order.status == order.Completed:
            if order.isbuy():
                self.log(
                    f"[BUY] Price: {order.executed.price:<10.2f} | "
                    f"Cost: {order.executed.value:<10.2f} | "
                    f"Comm: {order.executed.comm:<10.2f}"
                )
            elif order.issell():
                self.log(
                    f"[SELL] Price: {order.executed.price:<10.2f} | "
                    f"Cost: {order.executed.value:<10.2f} | "
                    f"Comm: {order.executed.comm:<10.2f}"
                )
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            status_map = {
                order.Canceled: "Canceled",
                order.Margin: "Margin",
                order.Rejected: "Rejected",
                order.Partial: "Partial",
            }
            status = status_map.get(order.status, "Unknown")
            self.log(f"[{order.data._name}] Order placement failed - status: {status}")

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        """
        Handle trade notifications.
        """
        if not trade.isclosed:
            return

        self.log(
            f"[OPERATION PROFIT] Gross: {trade.pnl:<10.2f} | "
            f"Net: {trade.pnlcomm:<10.2f}"
        )
