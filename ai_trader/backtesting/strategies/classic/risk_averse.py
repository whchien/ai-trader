import backtrader as bt

from ai_trader.backtesting.strategies.base import BaseStrategy
from ai_trader.backtesting.strategies.indicators import AverageVolatility, DiffHighLow, RecentHigh


class RiskAverseStrategy(BaseStrategy):
    """
    Risk Averse Strategy - Multi-factor selection of stable, liquid, trending stocks.

    Combines four independent conditions to identify high-quality trading opportunities
    with low volatility, upward momentum, high liquidity, and narrow price ranges.
    Entry requires ALL four conditions; exit triggers when 2+ conditions deteriorate.

    Entry Logic (Buy):
    - Condition 1: Low volatility (candle volatility < threshold)
    - Condition 2: Recent new high (bullish momentum)
    - Condition 3: High trading volume (>100K shares daily average)
    - Condition 4: Narrow price range (high/low spread < threshold)
    - Buy Signal: ALL four conditions must be true

    Exit Logic (Sell):
    - Exit when 2 or more conditions become false (safety margin)
    - Prevents holding through deteriorating market conditions

    Parameters:
    - volatility_period (int): Period for volatility calculation [default: 20]
    - high_low_period (int): Period for price range analysis [default: 60]
    - vol_period (int): Period for volume moving average [default: 5]
    - volatility_threshold (float): Maximum volatility to accept [default: 8]
    - high_low_threshold (float): Maximum high/low spread ratio [default: 0.3]

    Notes:
    - Multi-factor approach reduces correlation with market regime
    - Requires new highs + low volatility = trending consolidation
    - High volume filter ensures liquidity and conviction
    - Conservative exit (2+ conditions) allows some flexibility
    - Targets swing trades in quality stocks; 5-20 day typical holding
    """

    params = dict(
        volatility_period=20,
        high_low_period=60,
        vol_period=5,
        volatility_threshold=8,
        high_low_threshold=0.3,
    )

    def __init__(self):
        """Initialize volatility, volume, trend, and price range indicators."""
        self.candle_volatility = AverageVolatility(self.data, period=self.params.volatility_period)
        self.has_new_high = RecentHigh(self.data)
        self.past_vol = bt.indicators.SimpleMovingAverage(
            self.data.volume, period=self.params.vol_period
        )
        self.diff_high_low = DiffHighLow(self.data, period=self.params.high_low_period)

    def next(self):
        """Execute trading logic: buy on multiple low-risk conditions, exit on condition degradation."""
        # Conditions
        cond_1 = self.candle_volatility.avg_volatility[0] < self.params.volatility_threshold
        cond_2 = self.has_new_high.new_high[0] > 0
        cond_3 = self.past_vol[0] > 100 * 1000
        cond_4 = self.diff_high_low.diff[0] < self.params.high_low_threshold

        # Combined signals
        conditions = [cond_1, cond_2, cond_3, cond_4]
        buy_signal = all(conditions)
        close_signal = sum(not cond for cond in conditions) >= 2

        # Execute trades based on signals
        if self.position:
            if close_signal:
                self.close()
        elif buy_signal:
            self.buy()


if __name__ == "__main__":
    from ai_trader.utils.backtest import run_backtest

    # Run backtest with RiskAverseStrategy
    results = run_backtest(
        strategy=RiskAverseStrategy,
        data_source=None,  # Use example data
        cash=1000000,
        commission=0.001425,
    )

    print("Backtest completed! Use cerebro.plot() to visualize results.")
