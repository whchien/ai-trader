import backtrader as bt

from ai_trader.trader import AITrader
from ai_trader.strategy.base import BaseStrategy


class ROCRotationStrategy(BaseStrategy):
    params = dict(period=20)

    def __init__(self):
        self.indicators = {
            data: bt.ind.RateOfChange(data, period=self.params.period)
            for data in self.datas
        }

        self.num_of_holdings = 0
        self.top_k = 5

    def next(self):
        # 1. Select by signals
        # prepare quick lookup list of stocks currently holding a position
        holding = [d for d, pos in self.getpositions().items() if pos]
        to_buy = [data for data, roc in self.indicators.items() if roc[0] > 0.0]
        to_close = [data for data, roc in self.indicators.items() if roc[0] < 0.0]

        for data in to_close:
            if data in holding:
                self.order_target_percent(data=data, target=0.0)
                self.log("Leave {} ".format(data._name))
                holding.remove(data)

        portfolio = list(set(to_buy + holding))

        if len(portfolio) == 0:  # 无股票选中，则返回
            return

        else:
            # 2. Select top k
            if len(portfolio) > self.top_k:
                data_roc = {item: self.indicators[item][0] for item in portfolio}
                portfolio = sorted(
                    data_roc.items(),  # get the (d, rank), pair
                    key=lambda x: x[1],
                    reverse=True,  # highest ranked 1st
                )
                portfolio = portfolio[: self.top_k]
                portfolio = [item[0] for item in portfolio]
                print("portfolio", [p._name for p in portfolio])

            # 3. Weight equally 等权重分配, 已持仓的应应该不变，对cash对新增的等权分配
            weight = 1 / len(portfolio)
            for p in portfolio:
                if p in holding:  # 調整艙位
                    self.log("Rebal {} ".format(p._name))
                    self.order_target_percent(p, target=weight * 0.95)
                else:
                    self.log("Enter {} ".format(p._name))
                    self.order_target_percent(p, target=weight * 0.95)


if __name__ == "__main__":
    e = AITrader()
    e.cerebro.addstrategy(ROCRotationStrategy)
    e.run(data_type="portfolio", sizer=False)
    e.cerebro.plot(iplot=False)
