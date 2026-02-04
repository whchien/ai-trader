import backtrader as bt

from ai_trader.backtesting.strategies.base import BaseStrategy
from ai_trader.backtesting.strategies.indicators import AlphaRSIPro


class AlphaRSIProStrategy(BaseStrategy):
    """
    AlphaRSI Pro Strategy - Uses adaptive volatility levels and trend confirmation.

    Entry Logic (Buy):
    - Smoothed RSI crosses above adaptive oversold level (from below)
    - AND trend bias is positive (uptrend confirmed by SMA slope)

    Exit Logic (Sell):
    - Smoothed RSI crosses below adaptive overbought level (from above)
    - AND trend bias is negative (downtrend confirmed by SMA slope)

    This strategy only takes positions aligned with the underlying trend,
    significantly reducing false signals in choppy markets.

    Parameters:
    - rsi_period (int): RSI calculation period [default: 14]
    - smoothing_period (int): Period for smoothing RSI [default: 5]
    - smoothing_type (str): Type of smoothing (SMA/EMA) [default: "SMA"]
    - atr_period (int): ATR period for volatility measurement [default: 14]
    - atr_ma_period (int): Moving average period for ATR smoothing [default: 50]
    - trend_sma_period (int): SMA period for trend bias calculation [default: 50]
    - sensitivity (int): Sensitivity of level adaptation to volatility [default: 20]
    - ob_base (int): Base overbought level [default: 70]
    - os_base (int): Base oversold level [default: 30]
    - ob_min (int): Minimum overbought level in low volatility [default: 65]
    - ob_max (int): Maximum overbought level in high volatility [default: 85]
    - os_min (int): Minimum oversold level in low volatility [default: 15]
    - os_max (int): Maximum oversold level in high volatility [default: 35]

    Notes:
    - Adaptive levels adjust to volatility; wider in trending markets, tighter in choppy ones
    - Trend bias filter prevents counter-trend trades; significantly reduces drawdowns
    - RSI smoothing reduces noise while preserving crossover timing
    """

    params = dict(
        rsi_period=14,
        smoothing_period=5,
        smoothing_type="SMA",
        atr_period=14,
        atr_ma_period=50,
        trend_sma_period=50,
        sensitivity=20,
        ob_base=70,
        os_base=30,
        ob_min=65,
        ob_max=85,
        os_min=15,
        os_max=35,
    )

    def __init__(self):
        """Initialize AlphaRSI Pro with adaptive volatility levels and trend filter."""
        super().__init__()
        # Initialize the AlphaRSI Pro indicator with strategy parameters
        self.indicator = AlphaRSIPro(
            self.data,
            rsi_period=self.p.rsi_period,
            smoothing_period=self.p.smoothing_period,
            smoothing_type=self.p.smoothing_type,
            atr_period=self.p.atr_period,
            atr_ma_period=self.p.atr_ma_period,
            trend_sma_period=self.p.trend_sma_period,
            sensitivity=self.p.sensitivity,
            ob_base=self.p.ob_base,
            os_base=self.p.os_base,
            ob_min=self.p.ob_min,
            ob_max=self.p.ob_max,
            os_min=self.p.os_min,
            os_max=self.p.os_max,
        )

    def next(self):
        """Execute trading logic: buy on RSI oversold in uptrend, sell on overbought in downtrend."""
        # Extract indicator values
        rsi_smooth = self.indicator.rsi_smooth[0]
        os_level = self.indicator.os_level[0]
        ob_level = self.indicator.ob_level[0]
        trend_bias = self.indicator.trend_bias[0]

        # Check for crossover signals
        rsi_cross_up = (
            rsi_smooth > os_level and self.indicator.rsi_smooth[-1] <= self.indicator.os_level[-1]
        )
        rsi_cross_down = (
            rsi_smooth < ob_level and self.indicator.rsi_smooth[-1] >= self.indicator.ob_level[-1]
        )

        # Entry signal: RSI crosses above OS level in uptrend
        buy_signal = rsi_cross_up and trend_bias > 0

        # Exit signal: RSI crosses below OB level in downtrend
        sell_signal = rsi_cross_down and trend_bias < 0

        # Execute trades
        if self.position.size == 0:
            if buy_signal:
                self.buy()
        else:
            if sell_signal:
                self.close()


if __name__ == "__main__":
    from ai_trader.utils.backtest import run_backtest

    # Run backtest with AlphaRSIProStrategy
    results = run_backtest(
        strategy=AlphaRSIProStrategy,
        data_source=None,  # Use example data
        cash=1000000,
        commission=0.001425,
    )

    print("Backtest completed! Use cerebro.plot() to visualize results.")
