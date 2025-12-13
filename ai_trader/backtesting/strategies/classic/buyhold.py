from ai_trader.trader import AITrader
from ai_trader.backtesting.strategies.base import BaseStrategy


class BuyHoldStrategy(BaseStrategy):
    def next(self):
        if self.position.size == 0:
            self.buy()


if __name__ == "__main__":
    trader = AITrader()
    trader.add_strategy(BuyHoldStrategy)
    trader.run()
    trader.plot()
