import backtrader as bt
import numpy as np
import statsmodels.api as sm

from ai_trader.core.logging import get_logger

logger = get_logger(__name__)


class RSRS(bt.Indicator):
    """
    RSRS (Resistance Support Relative Strength)

    RSRS is an indicator that utilizes linear regression analysis to assess the relative strength of resistance and
    support levels in a security's price. It is based on the concept of fitting a straight line to a series of high and
    low prices over a specified period.

    The slope coefficient calculated by the linear regression model represents the relative strength between resistance
    and support. A positive slope indicates that resistance is stronger than support, suggesting a potential downtrend
    or bearish sentiment. Conversely, a negative slope suggests that support is stronger than resistance, indicating a
    potential uptrend or bullish sentiment.

    The R-squared value (R2) measures the goodness-of-fit of the linear regression model to the actual .etl points.
    It indicates how well the regression line explains the variation in the high prices based on the low prices.
    A higher R-squared value (closer to 1) suggests a better fit of the regression line to the .etl,
    indicating stronger trend reliability.

    The interpretation of the RSRS indicator involves analyzing the slope coefficient and R-squared value.
    A strong positive slope coupled with a high R-squared value may indicate a robust resistance level and a potential
    downtrend in the security's price. Conversely, a strong negative slope with a high R-squared value may suggest a
    robust support level and a potential uptrend.

    The formula for RSRS is:
    Highest Price = α + β × Lowest Price
    where the slope coefficient β represents the degree to which the highest price changes relative to the lowest price.
    When the lowest price changes by 1, the highest price changes by β. When the slope coefficient β is large,
    the support strength is greater than the resistance strength, indicating that the highest price's change is faster
    than the lowest price's change, and the upward movement of the price has more space. Conversely, when the slope
    coefficient β is small, the resistance strength is greater than the support strength, indicating that the highest
    price's change is slower than the lowest price's change, and the upward movement of the price is gradually weakened.

    To use RSRS as a timing indicator, it is compared with its own historical values to calculate the Z-Score
    standardization. The RSRS value is obtained by standardizing the current value relative to its historical values.
    This is done by taking M slope coefficients β and forming a sequence, calculating the mean and standard deviation
    of the sequence, and then calculating the Z-Score as (current value - mean) / standard deviation.

    Since the RSRS indicator has already undergone standardization, the .etl distribution follows a mean of 0 and a
    standard deviation of 1. The simplest approach is to take a long position when RSRS is above a threshold S and take
    a short position when RSRS is below -S.
    """

    lines = ("rsrs", "R2")

    def __init__(self, period: int = 18):
        self.high = self.data.high
        self.low = self.data.low
        self.period = period

    def next(self):
        high_n = self.high.get(ago=0, size=self.period)
        low_n = self.low.get(ago=0, size=self.period)

        try:
            x = sm.add_constant(np.array(low_n))
            model = sm.OLS(np.array(high_n), x)
            results = model.fit()
            self.lines.rsrs[0] = results.params[1]
            self.lines.R2[0] = results.rsquared
        except Exception as e:
            logger.warning(f"RSRS calculation failed, setting to 0: {e}")
            self.lines.rsrs[0] = 0


class NormRSRS(bt.Indicator):
    lines = ("rsrs_norm", "rsrs_r2", "beta_right")

    def __init__(self, period: int = 18, long_period: int = 600):
        self.rsrs = RSRS(self.data, period=period)
        self.lines.rsrs_norm = (
            self.rsrs - bt.ind.Average(self.rsrs, period=long_period)
        ) / bt.ind.StandardDeviation(self.rsrs, period=long_period)
        self.lines.rsrs_r2 = self.lines.rsrs_norm * self.rsrs.R2
        self.lines.beta_right = self.rsrs * self.lines.rsrs_r2


class RecentHigh(bt.Indicator):
    lines = ("new_high",)

    def __init__(self, short_period: int = 5, long_period: int = 100):
        self.addminperiod(long_period)
        self.short_period = short_period
        self.long_period = bt.indicators.Highest(self.data.close, period=long_period)

    def next(self):
        # Check if the closing price has made a new high in the past 5 days
        recent_highs = self.data.close.get(size=self.short_period)
        has_new_high = -1
        for recent_high in recent_highs:
            if recent_high >= self.long_period:
                has_new_high = 1
        self.lines.new_high[0] = has_new_high


class DailyCandleVolatility(bt.Indicator):
    lines = ("volatility", "avg_volatility")

    def __init__(self):
        self.close = self.data.close
        self.high = self.data.high
        self.low = self.data.low
        self.open = self.data.open
        self.bullish_candle = self.close >= self.open

    def next(self):
        if self.bullish_candle[0]:
            bullish_volatility = (
                abs(self.close[-1] - self.open[0])
                + abs(self.open[0] - self.low[0])
                + abs(self.low[0] - self.high[0])
                + abs(self.high[0] - self.close[0])
            )
            self.lines.volatility[0] = bullish_volatility
        else:
            bearish_volatility = (
                abs(self.close[-1] - self.open[0])
                + abs(self.open[0] - self.high[0])
                + abs(self.high[0] - self.low[0])
                + abs(self.low[0] - self.close[0])
            )
            self.lines.volatility[0] = bearish_volatility


class AverageVolatility(bt.Indicator):
    lines = ("volatility", "avg_volatility")

    def __init__(self, period: int):
        self.addminperiod(period)

        self.ma_close = bt.indicators.MovingAverageSimple(self.data.close, period=period)
        self.volatility = DailyCandleVolatility(self.data)
        self.ma_volatility = bt.indicators.MovingAverageSimple(self.volatility, period=period)
        self.lines.avg_volatility = self.ma_volatility / self.ma_close * 100

    def next(self):
        pass


class DiffHighLow(bt.Indicator):
    lines = ("diff",)

    def __init__(self, period: int = 60):
        self.addminperiod(period)
        self.lowest_low = bt.indicators.Lowest(self.data.low, period=period)
        self.highest_high = bt.indicators.Highest(self.data.high, period=period)
        self.lines.diff = 1 - self.lowest_low / self.highest_high

    def next(self):
        pass


class TripleRSI(bt.Indicator):
    lines = (
        "signal",
        "value",
    )

    def __init__(self, rsi_short, rsi_mid, rsi_long, oversold, overbought):
        self.rsi_short = bt.indicators.RSI(period=rsi_short)
        self.rsi_mid = bt.indicators.RSI(period=rsi_mid)
        self.rsi_long = bt.indicators.RSI(period=rsi_long)
        self.oversold = oversold
        self.overbought = overbought

    def next(self):
        value = 0

        # Long-term uptrend
        cond_1 = self.rsi_long[0] > self.oversold
        value += abs(self.rsi_long[0] - self.oversold)

        # Short-term not overheat
        cond_2 = self.rsi_mid[0] < self.overbought
        value += abs(self.rsi_mid[0] - self.overbought)

        # Short-term RSI at a high level and showing signs of consolidation
        recent_short_rsi = self.rsi_short.get(size=3)
        cond_3 = min([r > self.oversold for r in recent_short_rsi])

        # Short-term RSI in an uptrend
        cond_4 = (self.rsi_short[0] / self.rsi_short[-2] - 1) > 0.02
        value += abs(self.rsi_short[0] / self.rsi_short[-2])

        self.lines.signal[0] = 1 if cond_1 & cond_2 & cond_3 & cond_4 else -1
        self.lines.value[0] = value


class DoubleTop(bt.Indicator):
    """
    Double-Top Bullish Breakout Pattern Detector

    This indicator identifies a bullish breakout pattern where:
    1. A significant peak occurred 30-55 days ago (the "first top")
    2. Price pulled back, forming a trough in the last 30 days
    3. Price has broken out to match/exceed the first peak (the "second top")
    4. The breakout is confirmed by positive trend (both SMAs) and increasing volume

    Pattern Logic:
    - First top is the maximum price from 30-55 days ago
    - Pullback is confirmed by finding a low at least 5% below the first top
    - Current price must be at a recent 60-day high with 2% tolerance
    - Current price must break above the first top
    - Price must be above both short (60-day) and long (120-day) SMAs
    - Volume must be increasing (short-term MA > long-term MA)

    This pattern is called "DoubleTop" for consistency with the codebase, though
    it actually detects a bullish breakout (classic double-top is bearish).
    """

    lines = ("signal",)

    def __init__(
        self,
        sma_short: int = 60,
        sma_long: int = 120,
        vol_short: int = 5,
        vol_long: int = 20,
        past_highest: int = 60,
    ):
        self.addminperiod(sma_long)
        self.past_highest = bt.indicators.Highest(self.data.close, period=past_highest)
        self.sma_short = bt.indicators.MovingAverageSimple(self.data.close, period=sma_short)
        self.sma_long = bt.indicators.MovingAverageSimple(self.data.close, period=sma_long)
        self.vol_short = bt.indicators.MovingAverageSimple(self.data.volume, period=vol_short)
        self.vol_long = bt.indicators.MovingAverageSimple(self.data.volume, period=vol_long)

    def next(self):
        # Get the "first top" from the 30-55 day historical window
        try:
            historical_window = self.data.close.get(ago=30, size=25)
            if len(historical_window) < 25:
                self.lines.signal[0] = -1
                return
            first_top = max(historical_window)
        except (ValueError, IndexError):
            self.lines.signal[0] = -1
            return

        # Get pullback window (1-30 days ago) to find the trough
        try:
            pullback_window = self.data.close.get(ago=1, size=30)
            if len(pullback_window) < 30:
                self.lines.signal[0] = -1
                return
            pullback_low = min(pullback_window)
        except (ValueError, IndexError):
            self.lines.signal[0] = -1
            return

        # Condition 1: Today is at/near 60-day high (breakout)
        # Allow 2% tolerance for floating-point precision and minor variations
        cond_1 = self.data.close[0] >= self.past_highest[0] * 0.98

        # Condition 2: Meaningful pullback occurred (at least 5%)
        cond_2 = pullback_low < first_top * 0.95

        # Condition 3: First top is comparable to current price (within 10%)
        cond_3 = first_top >= self.data.close[0] * 0.90

        # Condition 4: Current price breaks above first top
        cond_4 = self.data.close[0] >= first_top

        # Condition 5: Price above short-term SMA (uptrend)
        cond_5 = self.data.close[0] > self.sma_short[0]

        # Condition 6: Price above long-term SMA (strong trend)
        cond_6 = self.data.close[0] > self.sma_long[0]

        # Condition 7: Volume increasing (breakout confirmation)
        cond_7 = self.vol_short[0] > self.vol_long[0]

        self.lines.signal[0] = (
            1 if cond_1 & cond_2 & cond_3 & cond_4 & cond_5 & cond_6 & cond_7 else -1
        )


class VCPPattern(bt.Indicator):
    """
    Key Concepts of Volatility Contraction Strategy (VCP):
    Volatility Contraction: Stocks exhibit a pattern where the price volatility decreases over time. This means that the
    trading range (the difference between the high and low prices) becomes narrower. The pattern usually consists of
    several waves of contraction, where each wave has a lower high and higher low compared to the previous wave.

    Volume Contraction: Alongside price contraction, there is a decrease in trading volume. This suggests that fewer
    traders are participating, which can precede a significant move when volume returns. A significant increase in
    volume during the breakout confirms the strength of the move.

    Breakout: After a period of contraction, the classic breaks out above a resistance level on increased volume.
    This breakout is the signal for traders to enter a position, anticipating a continued upward move.
    """

    lines = ("vcp",)

    def __init__(
        self,
        period_short: int = 10,
        period_long: int = 60,
        period_long_discount: float = 0.7,
        highest_close: int = 100,
        mean_vol: int = 20,
    ):
        # Volume reduction condition
        volume_short_avg = bt.indicators.MovingAverageSimple(self.data.volume, period=period_short)
        volume_long_avg = bt.indicators.MovingAverageSimple(self.data.volume, period=period_long)
        self.volume_reduce = volume_short_avg < (volume_long_avg * period_long_discount)

        # Price contraction condition
        price_short_std = bt.indicators.StandardDeviation(self.data.close, period=period_short)
        price_long_std = bt.indicators.StandardDeviation(self.data.close, period=period_long)
        self.price_contract = price_short_std < (price_long_std * period_long_discount)

        self.highest_close = bt.indicators.Highest(self.data.close, period=highest_close)
        self.mean_vol = bt.indicators.MovingAverageSimple(self.data.volume, period=mean_vol)

    def next(self):
        # Condition 1: Volume contraction and price contraction over the last 5 days
        # VCP = Volume Contraction Pattern, checks if both volume and price are contracting
        volume_reduce_5d = [i for i in self.volume_reduce.get(size=5)]
        price_contract_5d = [i for i in self.price_contract.get(size=5)]
        cond_1 = any(v > 0.0 and p > 0.0 for v, p in zip(volume_reduce_5d, price_contract_5d))

        # Condition 2: The current closing price must be the highest in the past 100 days
        # This indicates the classic is reaching a new high
        cond_2 = self.data.close[0] == self.highest_close[0]

        # Condition 3: The current volume must be greater than 80% of the 20-day average volume
        # This ensures there is sufficient trading activity
        cond_3 = self.data.volume[0] > self.mean_vol[0] * 0.8

        # Set the VCP line value to 1 if all conditions are met, otherwise set to -1
        self.lines.vcp[0] = 1 if cond_1 & cond_2 & cond_3 else -1


class AlphaRSIPro(bt.Indicator):
    """
    AlphaRSI Pro - Advanced RSI with adaptive volatility levels and trend confirmation.

    This indicator combines:
    1. Smoothed RSI to reduce noise
    2. Adaptive overbought/oversold levels based on market volatility (ATR)
    3. Trend bias filter using SMA slope to align signals with underlying trend

    The adaptive levels widen in high volatility (requiring more extreme readings) and
    narrow in low volatility (becoming more sensitive). Signals are only considered
    "strong" when aligned with the trend direction.
    """

    lines = ("rsi_smooth", "ob_level", "os_level", "trend_bias", "volatility_ratio")

    params = (
        ("rsi_period", 14),
        ("smoothing_period", 5),
        ("smoothing_type", "SMA"),
        ("atr_period", 14),
        ("atr_ma_period", 50),
        ("trend_sma_period", 50),
        ("sensitivity", 20),
        ("ob_base", 70),
        ("os_base", 30),
        ("ob_min", 65),
        ("ob_max", 85),
        ("os_min", 15),
        ("os_max", 35),
    )

    def __init__(self):
        # Calculate base RSI
        self.rsi = bt.indicators.RSI(period=self.p.rsi_period)

        # Apply smoothing to RSI
        if self.p.smoothing_type == "WMA":
            self.lines.rsi_smooth = bt.indicators.WeightedMovingAverage(
                self.rsi, period=self.p.smoothing_period
            )
        else:  # Default to SMA
            self.lines.rsi_smooth = bt.indicators.MovingAverageSimple(
                self.rsi, period=self.p.smoothing_period
            )

        # Calculate volatility ratio for adaptive levels
        self.atr = bt.indicators.ATR(period=self.p.atr_period)
        self.atr_ma = bt.indicators.MovingAverageSimple(self.atr, period=self.p.atr_ma_period)

        # Calculate trend bias using SMA
        self.trend_sma = bt.indicators.MovingAverageSimple(
            self.data.close, period=self.p.trend_sma_period
        )

        # Set minimum period
        self.addminperiod(
            max(
                self.p.rsi_period + self.p.smoothing_period,
                self.p.atr_ma_period,
                self.p.trend_sma_period,
            )
        )

    def next(self):
        try:
            # Calculate volatility ratio
            if self.atr_ma[0] > 0:
                vr = self.atr[0] / self.atr_ma[0]
            else:
                vr = 1.0
            self.lines.volatility_ratio[0] = vr

            # Calculate adaptive level adjustment
            adjustment = (vr - 1) * self.p.sensitivity

            # Apply adjustment and bounds to overbought level
            ob_adaptive = self.p.ob_base + adjustment
            self.lines.ob_level[0] = max(self.p.ob_min, min(self.p.ob_max, ob_adaptive))

            # Apply adjustment and bounds to oversold level
            os_adaptive = self.p.os_base - adjustment
            self.lines.os_level[0] = max(self.p.os_min, min(self.p.os_max, os_adaptive))

            # Calculate trend bias (+1 for uptrend, -1 for downtrend)
            if self.trend_sma[0] > self.trend_sma[-1]:
                self.lines.trend_bias[0] = 1
            else:
                self.lines.trend_bias[0] = -1

        except Exception as e:
            logger.warning(f"AlphaRSIPro calculation failed: {e}")
            self.lines.volatility_ratio[0] = 1.0
            self.lines.ob_level[0] = self.p.ob_base
            self.lines.os_level[0] = self.p.os_base
            self.lines.trend_bias[0] = 0


class AdaptiveRSI(bt.Indicator):
    """
    Adaptive RSI (ARSI) - RSI with dynamic period adaptation based on market conditions.

    This indicator adapts the RSI calculation period based on:
    1. Volatility ratio (ATR vs average ATR)
    2. Cycle detection (price change patterns)
    3. Market factor combining both metrics

    In high volatility or fast cycles, the period shortens (more responsive).
    In low volatility or slow cycles, the period lengthens (more stable).
    """

    lines = ("rsi", "adaptive_period", "volatility_ratio", "cycle_factor", "market_factor")

    params = (
        ("rsi_length", 14),
        ("atr_length", 14),
        ("min_period", 8),
        ("max_period", 28),
        ("adaptive_sensitivity", 1.0),
        ("smoothing_length", 3),
        ("ob_level", 70),
        ("os_level", 30),
        ("extreme_ob_level", 80),
        ("extreme_os_level", 20),
    )

    def __init__(self):
        # Calculate ATR for volatility measurement
        self.atr = bt.indicators.ATR(period=self.p.atr_length)
        self.atr_sma = bt.indicators.MovingAverageSimple(self.atr, period=self.p.atr_length)

        # Initialize state variables for RSI calculation
        self.avg_gain = None
        self.avg_loss = None

        # Calculate price changes for cycle detection
        self.price_diff = self.data.close - self.data.close(-1)

        # Set minimum period
        self.addminperiod(max(self.p.max_period, self.p.atr_length) + self.p.smoothing_length)

    def prenext(self):
        # Initialize avg_gain and avg_loss on first call with sufficient data
        if self.avg_gain is None and len(self) >= self.p.rsi_length:
            gains = []
            losses = []
            for i in range(-self.p.rsi_length + 1, 1):
                diff = self.data.close[i] - self.data.close[i - 1]
                if diff > 0:
                    gains.append(diff)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(-diff)

            self.avg_gain = np.mean(gains) if gains else 0.0
            self.avg_loss = np.mean(losses) if losses else 0.0

    def next(self):
        try:
            # Calculate volatility ratio
            if self.atr_sma[0] > 0:
                volatility_ratio = self.atr[0] / self.atr_sma[0]
            else:
                volatility_ratio = 1.0
            self.lines.volatility_ratio[0] = volatility_ratio

            # Calculate cycle factor
            if len(self) >= self.p.rsi_length:
                price_change = abs(self.data.close[0] - self.data.close[-self.p.rsi_length])

                # Calculate average of absolute price changes
                abs_changes = []
                for i in range(self.p.rsi_length):
                    if len(self) > i:
                        abs_changes.append(abs(self.data.close[-i] - self.data.close[-i - 1]))
                avg_price_change = np.mean(abs_changes) if abs_changes else 1.0

                if avg_price_change > 0:
                    cycle_factor = price_change / (avg_price_change * self.p.rsi_length)
                else:
                    cycle_factor = 0.0
            else:
                cycle_factor = 0.0
            self.lines.cycle_factor[0] = cycle_factor

            # Calculate market factor
            market_factor = (volatility_ratio + cycle_factor) / 2.0
            self.lines.market_factor[0] = market_factor

            # Calculate adaptive period (inverse relationship with market factor)
            period_range = self.p.max_period - self.p.min_period
            adaptive_period_float = self.p.max_period - (
                market_factor * period_range * self.p.adaptive_sensitivity / 10.0
            )
            adaptive_period = max(self.p.min_period, min(self.p.max_period, adaptive_period_float))
            self.lines.adaptive_period[0] = adaptive_period

            # Calculate RSI with adaptive period
            # Initialize if needed
            if self.avg_gain is None:
                self.avg_gain = 0.0
                self.avg_loss = 0.0

            # Calculate gain and loss for current bar
            price_diff = self.data.close[0] - self.data.close[-1]
            gain = price_diff if price_diff > 0 else 0.0
            loss = -price_diff if price_diff < 0 else 0.0

            # Update running averages with adaptive alpha
            alpha = 2.0 / (adaptive_period + 1.0)
            self.avg_gain = alpha * gain + (1.0 - alpha) * self.avg_gain
            self.avg_loss = alpha * loss + (1.0 - alpha) * self.avg_loss

            # Calculate RS and RSI
            if self.avg_loss != 0:
                rs = self.avg_gain / self.avg_loss
                rsi_raw = 100.0 - (100.0 / (1.0 + rs))
            else:
                rsi_raw = 100.0

            # Apply smoothing if configured
            if self.p.smoothing_length > 1:
                # Simple EMA smoothing
                if not hasattr(self, "rsi_ema"):
                    self.rsi_ema = rsi_raw
                else:
                    alpha_smooth = 2.0 / (self.p.smoothing_length + 1.0)
                    self.rsi_ema = alpha_smooth * rsi_raw + (1.0 - alpha_smooth) * self.rsi_ema
                self.lines.rsi[0] = self.rsi_ema
            else:
                self.lines.rsi[0] = rsi_raw

        except Exception as e:
            logger.warning(f"AdaptiveRSI calculation failed: {e}")
            self.lines.rsi[0] = 50.0
            self.lines.adaptive_period[0] = self.p.rsi_length
            self.lines.volatility_ratio[0] = 1.0
            self.lines.cycle_factor[0] = 0.0
            self.lines.market_factor[0] = 1.0


class HybridAlphaRSI(bt.Indicator):
    """
    Hybrid AlphaRSI - Most sophisticated RSI variant combining all enhancements.

    This indicator combines:
    1. Adaptive RSI period (from Adaptive RSI) - responds to volatility and cycles
    2. Adaptive overbought/oversold levels (from AlphaRSI Pro) - widens/narrows with volatility
    3. Trend bias filter (from AlphaRSI Pro) - aligns signals with underlying trend

    This is the most complex but potentially most effective approach, using dynamic
    calculation period AND dynamic thresholds with trend confirmation.
    """

    lines = (
        "rsi",
        "adaptive_period",
        "ob_level",
        "os_level",
        "trend_bias",
        "volatility_ratio",
        "market_factor",
    )

    params = (
        ("rsi_length", 14),
        ("atr_length", 14),
        ("atr_ma_period", 50),
        ("min_period", 8),
        ("max_period", 28),
        ("adaptive_sensitivity", 1.0),
        ("smoothing_length", 3),
        ("trend_sma_period", 50),
        ("level_sensitivity", 20),
        ("ob_base", 70),
        ("os_base", 30),
        ("ob_min", 65),
        ("ob_max", 85),
        ("os_min", 15),
        ("os_max", 35),
    )

    def __init__(self):
        # Calculate ATR for both volatility ratio and adaptive period
        self.atr = bt.indicators.ATR(period=self.p.atr_length)
        self.atr_sma_short = bt.indicators.MovingAverageSimple(self.atr, period=self.p.atr_length)
        self.atr_sma_long = bt.indicators.MovingAverageSimple(self.atr, period=self.p.atr_ma_period)

        # Calculate trend bias using SMA
        self.trend_sma = bt.indicators.MovingAverageSimple(
            self.data.close, period=self.p.trend_sma_period
        )

        # Initialize state variables for adaptive RSI calculation
        self.avg_gain = None
        self.avg_loss = None

        # Set minimum period
        self.addminperiod(
            max(
                self.p.max_period,
                self.p.atr_ma_period,
                self.p.trend_sma_period,
            )
            + self.p.smoothing_length
        )

    def prenext(self):
        # Initialize avg_gain and avg_loss on first call with sufficient data
        if self.avg_gain is None and len(self) >= self.p.rsi_length:
            gains = []
            losses = []
            for i in range(-self.p.rsi_length + 1, 1):
                diff = self.data.close[i] - self.data.close[i - 1]
                if diff > 0:
                    gains.append(diff)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(-diff)

            self.avg_gain = np.mean(gains) if gains else 0.0
            self.avg_loss = np.mean(losses) if losses else 0.0

    def next(self):
        try:
            # === Part 1: Calculate volatility ratio (for adaptive levels) ===
            if self.atr_sma_long[0] > 0:
                vr_levels = self.atr[0] / self.atr_sma_long[0]
            else:
                vr_levels = 1.0

            # === Part 2: Calculate market factor (for adaptive period) ===
            if self.atr_sma_short[0] > 0:
                vr_period = self.atr[0] / self.atr_sma_short[0]
            else:
                vr_period = 1.0

            # Calculate cycle factor
            if len(self) >= self.p.rsi_length:
                price_change = abs(self.data.close[0] - self.data.close[-self.p.rsi_length])

                # Calculate average of absolute price changes
                abs_changes = []
                for i in range(self.p.rsi_length):
                    if len(self) > i:
                        abs_changes.append(abs(self.data.close[-i] - self.data.close[-i - 1]))
                avg_price_change = np.mean(abs_changes) if abs_changes else 1.0

                if avg_price_change > 0:
                    cycle_factor = price_change / (avg_price_change * self.p.rsi_length)
                else:
                    cycle_factor = 0.0
            else:
                cycle_factor = 0.0

            # Calculate market factor
            market_factor = (vr_period + cycle_factor) / 2.0
            self.lines.market_factor[0] = market_factor
            self.lines.volatility_ratio[0] = vr_levels

            # === Part 3: Calculate adaptive period ===
            period_range = self.p.max_period - self.p.min_period
            adaptive_period_float = self.p.max_period - (
                market_factor * period_range * self.p.adaptive_sensitivity / 10.0
            )
            adaptive_period = max(self.p.min_period, min(self.p.max_period, adaptive_period_float))
            self.lines.adaptive_period[0] = adaptive_period

            # === Part 4: Calculate adaptive levels ===
            adjustment = (vr_levels - 1) * self.p.level_sensitivity

            ob_adaptive = self.p.ob_base + adjustment
            self.lines.ob_level[0] = max(self.p.ob_min, min(self.p.ob_max, ob_adaptive))

            os_adaptive = self.p.os_base - adjustment
            self.lines.os_level[0] = max(self.p.os_min, min(self.p.os_max, os_adaptive))

            # === Part 5: Calculate trend bias ===
            if self.trend_sma[0] > self.trend_sma[-1]:
                self.lines.trend_bias[0] = 1
            else:
                self.lines.trend_bias[0] = -1

            # === Part 6: Calculate RSI with adaptive period ===
            # Initialize if needed
            if self.avg_gain is None:
                self.avg_gain = 0.0
                self.avg_loss = 0.0

            # Calculate gain and loss for current bar
            price_diff = self.data.close[0] - self.data.close[-1]
            gain = price_diff if price_diff > 0 else 0.0
            loss = -price_diff if price_diff < 0 else 0.0

            # Update running averages with adaptive alpha
            alpha = 2.0 / (adaptive_period + 1.0)
            self.avg_gain = alpha * gain + (1.0 - alpha) * self.avg_gain
            self.avg_loss = alpha * loss + (1.0 - alpha) * self.avg_loss

            # Calculate RS and RSI
            if self.avg_loss != 0:
                rs = self.avg_gain / self.avg_loss
                rsi_raw = 100.0 - (100.0 / (1.0 + rs))
            else:
                rsi_raw = 100.0

            # Apply smoothing if configured
            if self.p.smoothing_length > 1:
                # Simple EMA smoothing
                if not hasattr(self, "rsi_ema"):
                    self.rsi_ema = rsi_raw
                else:
                    alpha_smooth = 2.0 / (self.p.smoothing_length + 1.0)
                    self.rsi_ema = alpha_smooth * rsi_raw + (1.0 - alpha_smooth) * self.rsi_ema
                self.lines.rsi[0] = self.rsi_ema
            else:
                self.lines.rsi[0] = rsi_raw

        except Exception as e:
            logger.warning(f"HybridAlphaRSI calculation failed: {e}")
            self.lines.rsi[0] = 50.0
            self.lines.adaptive_period[0] = self.p.rsi_length
            self.lines.ob_level[0] = self.p.ob_base
            self.lines.os_level[0] = self.p.os_base
            self.lines.trend_bias[0] = 0
            self.lines.volatility_ratio[0] = 1.0
            self.lines.market_factor[0] = 1.0
