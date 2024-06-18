import math

import backtrader as bt

from ai_trader.trader import AITrader
from ai_trader.strategy.base import BaseStrategy


class MultiTFStrategy(BaseStrategy):
    params = (("period", 20),)

    # states definition
    Empty, M15Hold, H1Hold, D1Hold = range(4)
    States = [
        "Empty",
        "M15Hold",
        "H1Hold",
        "D1Hold",
    ]

    def __init__(self):
        self.ma_m15 = bt.talib.SMA(self.dnames.m15, timeperiod=self.p.period)
        self.ma_h1 = bt.talib.SMA(self.dnames.h1, timeperiod=self.p.period)
        self.ma_d1 = bt.talib.SMA(self.dnames.d1, timeperiod=self.p.period)

        self.cross_m15 = bt.indicators.CrossOver(
            self.dnames.m15, self.ma_m15, plot=True
        )
        self.cross_h1 = bt.indicators.CrossOver(self.dnames.h1, self.ma_h1, plot=True)
        self.cross_d1 = bt.indicators.CrossOver(self.dnames.d1, self.ma_d1, plot=True)

        self.bsig_m15 = self.cross_m15 == 1
        self.bsig_h1 = self.cross_h1 == 1
        self.bsig_d1 = self.cross_d1 == 1
        self.sell_signal = self.cross_d1 == -1

        self.st = self.Empty
        self.st_map = {
            self.Empty: self._empty,
            self.M15Hold: self._m15hold,
            self.H1Hold: self._h1hold,
            self.D1Hold: self._d1hold,
        }

        # To keep track of pending orders
        self.order = None

    def next(self):
        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # just call state_map function
        self.order = self.st_map[self.st]()

        # Check if we are in the market and no buy order issued
        if self.position and not self.order:
            # Already in the market ... we might sell
            if self.sell_signal:
                self.st = self.Empty
                # Keep track of the created order to avoid a 2nd order
                self.order = self.close()

    def _empty(self):
        if self.bsig_m15:
            price = self.data0.close[0]
            cash = self.broker.get_cash()
            # 20% of the cash
            share = int(math.floor((0.2 * cash) / price))

            # set state
            self.st = self.H1Hold
            return self.buy(size=share)

    def _m15hold(self):
        if self.bsig_h1:
            price = self.data0.close[0]
            cash = self.broker.get_cash()

            share = int(math.floor((0.5 * cash) / price))

            # set state
            self.st = self.H1Hold
            return self.buy(size=share)

    def _h1hold(self):
        if self.bsig_h1:
            price = self.data0.close[0]
            cash = self.broker.get_cash()

            share = int(math.floor((0.5 * cash) / price))

            # set state
            self.st = self.D1Hold
            return self.buy(size=share)

    def _d1hold(self):
        return None


if __name__ == "__main__":
    engine = AITrader(data_type="ts")
    engine.add_strategy(MultiTFStrategy)
    engine.run()
    engine.plot()
