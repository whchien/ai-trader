"""
https://zhuanlan.zhihu.com/p/321149887

https://analyzingalpha.com/sector-momentum
https://school.stockcharts.com/doku.php?id=trading_strategies:sector_rotation_roc

"""

from datetime import datetime

import backtrader as bt
import numpy as np
from scipy.stats import linregress

from ai_trader.data import to_one_stock
from ai_trader.strategy.base import BaseStrategy


def momentum_func(self, price_array):
    r = np.log(price_array)
    slope, _, rvalue, _, _ = linregress(np.arange(len(r)), r)
    annualized = (1 + slope) ** 252
    return annualized * (rvalue**2)


# 定义动量指标
class Momentum(bt.ind.OperationN):
    lines = ("trend",)
    params = dict(period=90)
    func = momentum_func


class SectorMomentumRotationStrategy(BaseStrategy):
    params = dict(
        momentum=Momentum,
        momentum_period=180,
        num_positions=2,
        when=bt.timer.SESSION_START,
        timer=True,
        monthdays=[1],
        monthcarry=True,
        printlog=True,
    )

    def __init__(self):
        self.i = 0
        self.securities = self.datas[1:]
        self.inds = {}

        self.add_timer(
            when=self.p.when, monthdays=self.p.monthdays, monthcarry=self.p.monthcarry
        )

        for security in self.securities:
            self.inds[security] = self.p.momentum(
                security, period=self.p.momentum_period
            )

    def notify_timer(self, timer, when, *args, **kwargs):
        if self._getminperstatus() < 0:
            self.rebalance()

    def rebalance(self):
        rankings = list(self.securities)
        rankings.sort(key=lambda s: self.inds[s][0], reverse=True)
        pos_size = 1 / self.p.num_positions

        # Sell stocks no longer meeting ranking filter.
        for i, d in enumerate(rankings):
            if self.getposition(d).size:
                if i > self.p.num_positions:
                    self.close(d)

        # Buy and rebalance stocks with remaining cash
        for i, d in enumerate(rankings[: self.p.num_positions]):
            self.order_target_percent(d, target=pos_size)

    def next(self):
        self.notify_timer(self, self.p.timer, self.p.when)

    def stop(self):
        self.log(
            "| %2d | %2d |  %.2f |"
            % (self.p.momentum_period, self.p.num_positions, self.broker.getvalue()),
            doprint=True,
        )


if __name__ == "__main__":
    open_, high, low, close, adj_close, volume = load_tw_stocks()

    START_DATE = "2018-01-01"
    END_DATE = "2024-03-23"
    START = datetime.strptime(START_DATE, "%Y-%m-%d")
    END = datetime.strptime(END_DATE, "%Y-%m-%d")
    tickers = [
        "1101",
        "1102",
        "1103",
        #  '1104', '1107', '1108', '1109', '1110', '1201',
        # '1203', '1210', '1213', '1215', '1216', '1217', '1218', '1219', '1220',
        # '1225', '1227', '1229', '1231', '1232', '1233', '1234', '1235', '1236',
        # '1240', '1256', '1258'
    ]

    cerebro = bt.Cerebro()

    # # 加入标普基金SPY作为datas0，是基准
    # spy = dataframe.loc['SPY']
    # benchdata = bt.feeds.PandasData(dataname=spy, name='spy', plot=True)
    # cerebro.adddata(benchdata)
    # dataframe.drop('SPY', level='ticker', inplace=True)

    # 加入其他基金:
    for ticker in tickers:
        df = to_one_stock(ticker, open_, high, low, close, adj_close, volume)
        print(f"Adding ticker: {ticker}")
        data = bt.feeds.PandasData(dataname=df, name=ticker, plot=False)
        # .data.plotinfo.plotmaster = benchdata
        cerebro.adddata(data)

    cerebro.broker.setcash(3000000)
    print("Starting Portfolio Value: %.2f" % cerebro.broker.getvalue())

    # 加入策略（优化参数）
    stop = len(tickers) + 1
    cerebro.addstrategy(SectorMomentumRotationStrategy)
    cerebro.run()
    cerebro.plot(volume=False)

    # cerebro.optstrategy(SectorMomentumRotationStrategy,
    #                     momentum_period=range(50, 300, 50),
    #                     num_positions=range(1, len(tickers) + 1))
    #
    # # Run the strategy. Results will be output from stop.
    # cerebro.run(stdstats=False, tradehistory=False)
