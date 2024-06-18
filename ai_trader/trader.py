import os
from pathlib import Path

import backtrader as bt
import pandas as pd

from ai_trader.data.load import load_test, load_tw_stocks, to_one_stock
from ai_trader.strategy.base import BaseStrategy

COMPLETE_TICKERS = [
    "1565",
    "1569",
    "1815",
    "3078",
    "3083",
    "3088",
    "3202",
    "3211",
    "3213",
    "3218",
    "3227",
    "3260",
    "3290",
    "3293",
    "3313",
    "3324",
    "3325",
    "3388",
    "3402",
    "3483",
    "4105",
    "4111",
    "4121",
    "4127",
    "4129",
    "4401",
    "4417",
    "4707",
    "4721",
    "4908",
    "4909",
    "5015",
    "5347",
    "5355",
    "5425",
    "5426",
    "5439",
    "5452",
    "5488",
    "5490",
    "5508",
    "5512",
    "5530",
    "5609",
    "5905",
    "6104",
    "6118",
    "6123",
    "6125",
    "6126",
    "6127",
    "6129",
    "6143",
    "6146",
    "6147",
    "6160",
    "6163",
    "6170",
    "6180",
    "6182",
    "6187",
    "6188",
    "6223",
    "6231",
    "6233",
    "6234",
    "6237",
    "6245",
    "6261",
    "6263",
    "6274",
    "6279",
    "6290",
    "6508",
    "6509",
    "6609",
    "8049",
    "8054",
    "8064",
    "8069",
    "8076",
    "8088",
    "8092",
    "8096",
    "8099",
    "8109",
    "8121",
    "8182",
    "8183",
    "8255",
    "8299",
    "8383",
    "8930",
    "8936",
]


class AITrader:
    def __init__(self):
        self.cerebro = bt.Cerebro()
        self.start_date = None
        self.end_date = None
        self.rebalance_freq = "D"

    def log(self, txt: str):
        print(txt)

    def add_strategy(self, strategy: BaseStrategy):
        self.cerebro.addstrategy(strategy)
        self.log("Add strategy.")

    def add_data(self):
        df = load_test()
        feed = bt.feeds.PandasData(
            dataname=df,
            openinterest=None,
            timeframe=bt.TimeFrame.Days,
        )
        self.cerebro.adddata(feed)
        self.log("Load one individual .data.")

    def add_datas(self, resample_to_m: bool = False):
        open_, high, low, close, adj_close, volume = load_tw_stocks()

        tickers = COMPLETE_TICKERS  # [:30]

        for ticker in tickers:
            df = to_one_stock(ticker, open_, high, low, close, adj_close, volume)
            df = df["2020":"2024"]

            if resample_to_m:
                df = df.resample("M").last()
                data = bt.feeds.PandasData(
                    dataname=df, name=ticker, timeframe=bt.TimeFrame.Months, plot=False
                )
            else:
                data = bt.feeds.PandasData(
                    dataname=df, name=ticker, timeframe=bt.TimeFrame.Days, plot=False
                )

            self.cerebro.adddata(data, name=ticker)

        self.log(f"Added tickers: {tickers}")

    def add_ts_data(self):
        datapath = Path(os.getcwd()) / "./.data/2303.csv"
        df = pd.read_csv(datapath, parse_dates=["Date"], index_col=["Date"])

        data = bt.feeds.PandasData(
            dataname=df,
            openinterest=None,
            timeframe=bt.TimeFrame.Minutes,
            compression=15,
        )
        self.cerebro.adddata(data, name="m15")
        self.cerebro.resampledata(
            data, name="h1", compression=60, timeframe=bt.TimeFrame.Minutes
        )
        self.cerebro.resampledata(data, name="d1", timeframe=bt.TimeFrame.Days)

    def add_analyzers(self) -> None:
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="SharpeRatio")
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name="DrawDown")
        self.cerebro.addanalyzer(bt.analyzers.Returns, _name="Returns")
        # self.cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name="AnnualReturn")
        # self.cerebro.addanalyzer(bt.analyzers.SQN, _name="SystemQualityNumber")
        # self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="TradeAnalyzer")
        # self.cerebro.addanalyzer(bt.analyzers.PyFolio, _name='PyFolio')
        self.log("Set up analyzers.")

    def add_broker(self):
        self.cerebro.broker.setcash(1000000.0)
        self.cerebro.broker.setcommission(0.001425)
        # self.cerebro.broker.set_coc(True)
        self.log(f"Starting Value: {self.cerebro.broker.getvalue()}")

    def add_sizer(self):
        # self.cerebro.addsizer(bt.sizers.FixedSize, stake=1)
        # cerebro.addsizer(bt.sizers.AllInSizerInt, percents=10)
        self.cerebro.addsizer(bt.sizers.PercentSizer, percents=95)
        self.log("Set up sizer.")

    def analyze(self, result):
        self.log(f"Ending value: {round(self.cerebro.broker.getvalue())}")

        returns = result[0].analyzers.Returns.get_analysis()
        self.log(f"Total Returns: {round(returns['rtot'],2)}")
        self.log(f"Normalized Returns: {round(returns['rnorm'],2)}")

        sharpe = result[0].analyzers.SharpeRatio.get_analysis()["sharperatio"]
        self.log(f"Sharpe: {round(sharpe,2)}")

        drawdown = result[0].analyzers.DrawDown.get_analysis()["max"]["drawdown"]
        self.log(f"Drawdown: {round(drawdown,2)}")

    def run(self, data_type: str = "individual", sizer: bool = True):
        if data_type == "individual":
            self.add_data()

        elif data_type == "portfolio":
            self.add_datas()

        elif data_type == "ts":
            self.add_ts_data()
        else:
            raise "Not support"

        self.add_broker()

        if sizer:
            self.add_sizer()

        self.add_analyzers()

        result = self.cerebro.run()
        self.analyze(result)

    def plot(self):
        self.cerebro.plot()
