import backtrader as bt

from ai_trader.core.logging import get_logger

logger = get_logger(__name__)


class BaseStrategy(bt.Strategy):
    # Define column widths for consistent formatting
    COL_WIDTH_ACTION = 15
    COL_WIDTH_DETAIL1 = 20
    COL_WIDTH_DETAIL2 = 20
    COL_WIDTH_DETAIL3 = 20

    def __init__(self):
        super().__init__()
        # Log all strategy parameters (filter out methods and private attributes)
        params_dict = {
            key: getattr(self.params, key)
            for key in dir(self.params)
            if not key.startswith("_") and not callable(getattr(self.params, key))
        }
        if params_dict:
            params_str = ", ".join(f"{k}={v}" for k, v in params_dict.items())
            logger.info(f"{self.__class__.__name__} initialized with {params_str}")
        else:
            logger.info(f"{self.__class__.__name__} initialized with no parameters")

    def log(self, txt, dt=None):
        """
        Log the provided text with the backtest date.
        """
        dt = dt or self.datas[0].datetime.date(0)
        logger.info(f"{dt.isoformat()} │ {txt}")

    def notify_order(self, order):
        """
        Handle order notifications.
        """
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        if order.status == order.Completed:
            if order.isbuy():
                action_str = f"{'▲ BUY':<{self.COL_WIDTH_ACTION}}"
                detail1_str = f"Price: ${order.executed.price:>8.2f}"
                detail2_str = f"Value: ${order.executed.value:>11,.2f}"
                detail3_str = f"Commission: ${order.executed.comm:>6.2f}"

                # Pad the detail strings to their fixed widths
                padded_detail1 = f"{detail1_str:<{self.COL_WIDTH_DETAIL1}}"
                padded_detail2 = f"{detail2_str:<{self.COL_WIDTH_DETAIL2}}"
                padded_detail3 = f"{detail3_str:<{self.COL_WIDTH_DETAIL3}}"

                self.log(
                    f"{action_str} │ {padded_detail1} │ {padded_detail2} │ {padded_detail3}"
                )
            elif order.issell():
                action_str = f"{'▼ SELL':<{self.COL_WIDTH_ACTION}}"
                detail1_str = f"Price: ${order.executed.price:>8.2f}"
                detail2_str = f"Value: ${order.executed.value:>11,.2f}"
                detail3_str = f"Commission: ${order.executed.comm:>6.2f}"

                # Pad the detail strings to their fixed widths
                padded_detail1 = f"{detail1_str:<{self.COL_WIDTH_DETAIL1}}"
                padded_detail2 = f"{detail2_str:<{self.COL_WIDTH_DETAIL2}}"
                padded_detail3 = f"{detail3_str:<{self.COL_WIDTH_DETAIL3}}"

                self.log(
                    f"{action_str} │ {padded_detail1} │ {padded_detail2} │ {padded_detail3}"
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
            action_str = f"{'✗ ORDER FAILED':<{self.COL_WIDTH_ACTION}}"
            detail1_str = f"Status: {status}"

            # Pad the detail string
            padded_detail1 = f"{detail1_str:<{self.COL_WIDTH_DETAIL1}}"
            padded_detail2 = f"{'':<{self.COL_WIDTH_DETAIL2}}" # Empty for this type of log
            padded_detail3 = f"{'':<{self.COL_WIDTH_DETAIL3}}" # Empty for this type of log

            self.log(f"{action_str} │ {padded_detail1} │ {padded_detail2} │ {padded_detail3}")


        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        """
        Handle trade notifications.
        """
        if not trade.isclosed:
            return

        profit_symbol = "+" if trade.pnlcomm > 0 else "-"
        action_str = f"{f'{profit_symbol} P&L':<{self.COL_WIDTH_ACTION}}"
        detail1_str = f"Gross: ${trade.pnl:>10,.2f}"
        detail2_str = f"Net: ${trade.pnlcomm:>10,.2f}"

        padded_detail1 = f"{detail1_str:<{self.COL_WIDTH_DETAIL1}}"
        padded_detail2 = f"{detail2_str:<{self.COL_WIDTH_DETAIL2}}"
        padded_detail3 = f"{'':<{self.COL_WIDTH_DETAIL3}}" # Empty for P&L logs

        self.log(
            f"{action_str} │ {padded_detail1} │ {padded_detail2} │ {padded_detail3}"
        )
