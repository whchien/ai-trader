from __future__ import absolute_import, division, print_function, unicode_literals

import backtrader as bt
from loguru import logger

from ai_trader.strategy.base import BaseStrategy


class MultiBollingerBandsStrategy(BaseStrategy):
    def __init__(self):
        self.inds = {}
        for data in self.datas:
            self.inds[data] = {}
            top = bt.indicators.BollingerBands(data, period=20).top
            self.inds[data]["buy"] = data.close - top
            bot = bt.indicators.BollingerBands(data, period=20).bot
            self.inds[data]["sell"] = data.close - bot

    def next(self):
        # 判断当前已经持仓
        to_buy = []
        to_sell = []
        holding = []
        for data, ind in self.inds.items():
            if ind["buy"][0] > 0:
                to_buy.append(data)

            if ind["sell"][0] < 0:
                to_sell.append(data)

            if self.getposition(data).size > 0:
                holding.append(data)

        for sell in to_sell:
            if self.getposition(sell).size > 0:
                logger.debug("清仓" + sell.p.name)
                self.close(sell)

        new_hold = list(set(to_buy + holding))

        for data in to_sell:
            if data in new_hold:
                new_hold.remove(data)

        K = 1
        if len(new_hold) > K:
            data_roc = {}
            for item in new_hold:
                data_roc[item] = self.inds[item][0]
            # 排序
            new_hold = sorted(data_roc.items(), key=lambda x: x[1], reverse=True)
            new_hold = new_hold[:K]
            new_hold = [item[0] for item in new_hold]

        # 等权重分配 todo: 已持仓的应应该不变，对cash对新增的等权分配
        if len(new_hold) > 0:
            weight = 1 / len(new_hold)
            for data in new_hold:
                self.order_target_percent(data, weight * 0.99)
