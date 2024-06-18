import argparse
import datetime
import glob
import os.path

import backtrader as bt

from ai_trader.trader import AITrader
from ai_trader.strategy.base import BaseStrategy


class NetPayOutData(bt.feeds.GenericCSVData):
    lines = ("npy",)  # add a line containing the net payout yield
    params = dict(
        npy=6,  # npy field is in the 6th column (0 based index)
        dtformat="%Y-%m-%d",  # fix date format a yyyy-mm-dd
        timeframe=bt.TimeFrame.Months,  # fixed the timeframe
        openinterest=-1,  # -1 indicates there is no openinterest field
    )


class St(BaseStrategy):
    params = dict(
        selcperc=0.10,  # percentage of stocks to select from the universe
        rperiod=1,  # period for the returns calculation, default 1 period
        vperiod=36,  # lookback period for volatility - default 36 periods
        mperiod=12,  # lookback period for momentum - default 12 periods
        reserve=0.05,  # 5% reserve capital
    )

    def __init__(self):
        # calculate 1st the amount of stocks that will be selected
        self.selnum = int(len(self.datas) * self.p.selcperc)

        # allocation perc per indiv
        # reserve kept to make sure orders are not rejected due to
        # margin. Prices are calculated when known (close), but orders can only
        # be executed next day (opening price). Price can gap upwards
        self.perctarget = (1.0 - self.p.reserve) / self.selnum

        # returns, volatilities and momentums
        rs = [bt.ind.PctChange(d, period=self.p.rperiod) for d in self.datas]
        vs = [bt.ind.StdDev(ret, period=self.p.vperiod) for ret in rs]
        ms = [bt.ind.ROC(d, period=self.p.mperiod) for d in self.datas]

        # simple rank formula: (momentum) / volatility
        # the highest ranked: low vol, large momentum
        self.ranks = {data: m / v for data, v, m in zip(self.datas, vs, ms)}

    def next(self):
        # sort .data and current rank
        ranks = sorted(
            self.ranks.items(),  # get the (d, rank), pair
            key=lambda x: x[1][0],  # use rank (elem 1) and current time "0"
            reverse=True,  # highest ranked 1st ... please
        )

        # put top ranked in dict with .data as key to test for presence
        rtop = dict(ranks[: self.selnum])

        # For logging purposes of stocks leaving the portfolio
        rbot = dict(ranks[self.selnum :])

        # prepare quick lookup list of stocks currently holding a position
        posdata = [d for d, pos in self.getpositions().items() if pos]

        # remove those no longer top ranked
        # do this first to issue sell orders and free cash
        for d in (d for d in posdata if d not in rtop):
            self.log("Leave {} - Rank {:.2f}".format(d._name, rbot[d][0]))
            self.order_target_percent(d, target=0.0)

        # rebalance those already top ranked and still there
        for d in (d for d in posdata if d in rtop):
            self.log("Rebal {} - Rank {:.2f}".format(d._name, rtop[d][0]))
            self.order_target_percent(d, target=self.perctarget)
            del rtop[d]  # remove it, to simplify next iteration

        # issue a target order for the newly top ranked stocks
        # do this last, as this will generate buy orders consuming cash
        for d in rtop:
            self.log("Enter {} - Rank {:.2f}".format(d._name, rtop[d][0]))
            self.order_target_percent(d, target=self.perctarget)


if __name__ == "__main__":
    e = AITrader()
    e.cerebro.addstrategy(St)
    e.run(data_type="portfolio")
