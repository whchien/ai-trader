import glob
import os
from typing import Optional, List

import backtrader as bt
import pandas as pd

from ai_trader.loader import load_example
from ai_trader.strategy.base import BaseStrategy
from ai_trader.utils import extract_ticker_from_path


class AITrader:
    """
    AITrader is a wrapper for Backtrader functions, designed to accelerate the strategy development process.
    """

    def __init__(
        self,
        strategy: Optional[BaseStrategy] = None,
        cash: int = 1000000,
        commission: float = 0.001425,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        data_dir: Optional[str] = "./data/tw_stock/",
    ):
        """
        Initializes the AITrader with the given parameters.
        """
        self.cash = cash
        self.commission = commission
        self.start_date = start_date
        self.end_date = end_date
        self.strategy = strategy
        self.data_dir = data_dir
        self.cerebro = bt.Cerebro()

    def log(self, txt: str) -> None:
        """
        Logs a message to the console.
        """
        print(txt)

    def add_strategy(self, strategy: BaseStrategy) -> None:
        """
        Adds a trading strategy to the cerebro instance.
        """
        self.strategy = strategy
        self.cerebro.addstrategy(strategy)
        self.log("Strategy added.")

    def add_one_stock(self, df: Optional[pd.DataFrame] = None) -> None:
        """
        Loads classic test data into the cerebro instance.
        """
        if df is None:
            df = load_example()

        df = df[self.start_date : self.end_date]
        feed = bt.feeds.PandasData(
            dataname=df,
            openinterest=None,
            timeframe=bt.TimeFrame.Days,
        )
        self.cerebro.adddata(feed)
        self.log("Data loaded.")

    def add_stocks(self, date_col: str = "date") -> None:
        """
        Loads portfolio data for multiple stocks into the cerebro instance.
        """
        files = glob.glob(os.path.join(self.data_dir, "*.csv"))

        for file in files:
            df = pd.read_csv(file, parse_dates=[date_col], index_col=[date_col])
            df = df[self.start_date : self.end_date]
            ticker = extract_ticker_from_path(file)
            data = bt.feeds.PandasData(
                dataname=df, name=ticker, timeframe=bt.TimeFrame.Days, plot=False
            )
            self.cerebro.adddata(data, name=ticker)

    def add_analyzers(self) -> None:
        """
        Adds analyzers to the cerebro instance.
        """
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="SharpeRatio")
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name="DrawDown")
        self.cerebro.addanalyzer(bt.analyzers.Returns, _name="Returns")
        self.log("Analyzers added.")

    def add_broker(self) -> None:
        """
        Configures the broker settings.
        """
        self.cerebro.broker.setcash(self.cash)
        self.cerebro.broker.setcommission(commission=self.commission)
        self.log(f"Starting Value: {self.cerebro.broker.getvalue()}")

    def add_sizer(self) -> None:
        """
        Sets the sizer for position sizing.
        """
        self.cerebro.addsizer(bt.sizers.PercentSizer, percents=95)
        self.log("Sizer set to 95%.")

    def analyze(self, result: List[bt.Strategy]) -> None:
        """
        Analyzes the results of the backtest.
        """
        self.log(f"Ending value: {round(self.cerebro.broker.getvalue())}")

        returns = result[0].analyzers.Returns.get_analysis()
        self.log(f"Total Returns: {round(returns['rtot'], 2)}")
        self.log(f"Normalized Returns: {round(returns['rnorm'], 2)}")

        sharpe = result[0].analyzers.SharpeRatio.get_analysis().get("sharperatio")
        if sharpe:
            self.log(f"Sharpe Ratio: {round(sharpe, 2)}")

        drawdown = (
            result[0].analyzers.DrawDown.get_analysis().get("max", {}).get("drawdown")
        )
        if drawdown:
            self.log(f"Max Drawdown: {round(drawdown, 2)}")

    def run(self) -> None:
        """
        Runs the backtest with the specified data type and sizer.
        """
        if self.strategy:
            self.add_stocks()
            self.add_broker()
            self.add_sizer()
            self.add_analyzers()
            result = self.cerebro.run()
            self.analyze(result)
        else:
            raise ValueError("No strategy specified.")

    def plot(self) -> None:
        """
        Plots the results of the backtest.
        """
        self.cerebro.plot()
