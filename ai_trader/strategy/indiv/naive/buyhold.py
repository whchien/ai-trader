from ai_trader.trader import AITrader
from ai_trader.strategy.base import BaseStrategy


class BuyHoldStrategy(BaseStrategy):
    def next(self):
        if self.position.size == 0:
            self.buy()


if __name__ == "__main__":
    engine = AITrader()
    engine.add_strategy(BuyHoldStrategy)
    engine.run()
    engine.plot()
