import backtrader as bt
import numpy as np
import statsmodels.api as sm


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

    The R-squared value (R2) measures the goodness-of-fit of the linear regression model to the actual .data points.
    It indicates how well the regression line explains the variation in the high prices based on the low prices.
    A higher R-squared value (closer to 1) suggests a better fit of the regression line to the .data,
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

    Since the RSRS indicator has already undergone standardization, the .data distribution follows a mean of 0 and a
    standard deviation of 1. The simplest approach is to take a long position when RSRS is above a threshold S and take
    a short position when RSRS is below -S.
    """

    lines = ("rsrs", "R2")

    params = (("N", 18), ("value", 5))

    def __init__(self):
        self.high = self.data.high
        self.low = self.data.low

    def next(self):
        high_n = self.high.get(ago=0, size=self.p.N)
        low_n = self.low.get(ago=0, size=self.p.N)

        try:
            X = sm.add_constant(np.array(low_n))
            model = sm.OLS(np.array(high_n), X)
            results = model.fit()
            self.lines.rsrs[0] = results.params[1]
            self.lines.R2[0] = results.rsquared
        except:
            self.lines.rsrs[0] = 0


class NormRSRS(bt.Indicator):
    lines = ("rsrs_norm", "rsrs_r2", "beta_right")
    params = (("N", 18), ("M", 600))

    def __init__(self):
        self.rsrs = RSRS(self.data)
        self.lines.rsrs_norm = (
            self.rsrs - bt.ind.Average(self.rsrs, period=self.p.M)
        ) / bt.ind.StandardDeviation(self.rsrs, period=self.p.M)
        self.lines.rsrs_r2 = self.lines.rsrs_norm * self.rsrs.R2
        self.lines.beta_right = self.rsrs * self.lines.rsrs_r2


class NewHighIn5Days(bt.Indicator):
    lines = ("new_high",)

    def __init__(self):
        self.addminperiod(100)
        self.past_100_high = bt.indicators.Highest(self.data.close, period=100)

    def next(self):
        # Check if the closing price has made a new high in the past 5 days
        recent_highs = self.data.close.get(size=5)
        has_new_high = -1
        for recent_high in recent_highs:
            if recent_high >= self.past_100_high:
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

        self.ma_close = bt.indicators.MovingAverageSimple(
            self.data.close, period=period
        )
        self.volatility = DailyCandleVolatility(self.data)
        self.ma_volatility = bt.indicators.MovingAverageSimple(
            self.volatility, period=period
        )
        self.lines.avg_volatility = self.ma_volatility / self.ma_close * 100

    def next(self):
        pass


class DiffHighLow(bt.Indicator):
    lines = ("diff",)

    def __init__(self):
        self.addminperiod(60)
        self.lowest_low = bt.indicators.Lowest(self.data.low, period=60)
        self.highest_high = bt.indicators.Highest(self.data.high, period=60)
        self.lines.diff = 1 - self.lowest_low / self.highest_high

    def next(self):
        pass


class TripleRSI(bt.Indicator):
    lines = (
        "signal",
        "value",
    )
    params = (
        ("rsi_short", 20),
        ("rsi_mid", 60),
        ("rsi_long", 120),
        ("oversold", 55),
        ("overbought", 75),
    )

    def __init__(self):
        self.rsi_short = bt.indicators.RSI(period=self.params.rsi_short)
        self.rsi_mid = bt.indicators.RSI(period=self.params.rsi_mid)
        self.rsi_long = bt.indicators.RSI(period=self.params.rsi_long)

    def next(self):
        value = 0

        # Long-term uptrend
        cond_1 = self.rsi_long[0] > self.params.oversold
        value += abs(self.rsi_long[0] - self.params.oversold)

        # Short-term not overheat
        cond_2 = self.rsi_mid[0] < self.params.overbought
        value += abs(self.rsi_mid[0] - self.params.overbought)

        # Short-term RSI at a high level and showing signs of consolidation
        recent_short_rsi = self.rsi_short.get(size=3)
        cond_3 = min([r > self.params.oversold for r in recent_short_rsi])

        # Short-term RSI in an uptrend
        cond_4 = (self.rsi_short[0] / self.rsi_short[-2] - 1) > 0.02
        value += abs(self.rsi_short[0] / self.rsi_short[-2])

        self.lines.signal[0] = 1 if cond_1 & cond_2 & cond_3 & cond_4 else -1
        self.lines.value[0] = value


class DoubleTop(bt.Indicator):
    lines = ("signal",)

    def __init__(self):
        self.addminperiod(120)
        self.highest_60 = bt.indicators.Highest(self.data.close, period=60)
        self.sma_60 = bt.indicators.MovingAverageSimple(self.data.close, period=60)
        self.sma_120 = bt.indicators.MovingAverageSimple(self.data.close, period=120)
        self.vol_short = bt.indicators.MovingAverageSimple(self.data.volume, period=5)
        self.vol_long = bt.indicators.MovingAverageSimple(self.data.volume, period=20)

    def next(self):
        # Condition 1: Close price makes a new 60-day high
        cond_1 = self.data.close[0] == self.highest_60

        # Condition 2: At least one day in the previous 30 days did not make a new high
        cond_2 = any(
            [p for p in self.data.close.get(ago=1, size=30) if p < self.highest_60]
        )

        # Condition 3: At least one day in the 30th to 55th day before today made a new 60-day high
        cond_3 = any(
            [p for p in self.data.close.get(ago=30, size=25) if p > self.highest_60]
        )

        # Condition 4: Maximum close price in the 30th to 55th day before today is less than today's close
        try:
            highest_past = max([p for p in self.data.close.get(ago=25, size=25)])
            cond_4 = highest_past < self.data.close[0]
        except ValueError:
            cond_4 = True

        # Condition 5: Close price is greater than the close price 120 days ago
        cond_5 = self.data.close[0] > self.sma_60[0]  # self..data.close[-120]

        # Condition 6: Close price is greater than the close price 60 days ago
        cond_6 = self.data.close[0] > self.sma_120[0]  # self..data.close[-60]

        cond_7 = self.vol_short[0] > self.vol_long[0]

        if cond_4:
            print(cond_1, cond_2, cond_3, cond_5, cond_6)

        self.lines.signal[0] = (
            1 if cond_1 & cond_2 & cond_3 & cond_5 & cond_6 & cond_7 else -1
        )


class VolatilityContractionPattern(bt.Indicator):
    lines = ("vcp",)

    params = (
        ("period_short", 10),
        ("period_long", 60),
        ("period_long_discount", 0.7),
        ("sustain_period", 5),
        ("min_volume_ratio", 0.8),
    )

    def __init__(self):
        # Volume reduction condition
        volume_short_avg = bt.indicators.MovingAverageSimple(
            self.data.volume, period=self.params.period_short
        )
        volume_long_avg = bt.indicators.MovingAverageSimple(
            self.data.volume, period=self.params.period_long
        )
        self.volume_reduce = volume_short_avg < (
            volume_long_avg * self.params.period_long_discount
        )

        # Price contraction condition
        price_short_std = bt.indicators.StandardDeviation(
            self.data.close, period=self.params.period_short
        )
        price_long_std = bt.indicators.StandardDeviation(
            self.data.close, period=self.params.period_long
        )
        self.price_contract = price_short_std < (
            price_long_std * self.params.period_long_discount
        )

        self.price_past_100_high = bt.indicators.Highest(self.data.close, period=20)
        self.vol_20_mean = bt.indicators.MovingAverageSimple(
            self.data.volume, period=20
        )

    def next(self):
        # Condition 1: Volume contraction and price contraction over the last 5 days
        # VCP = Volume Contraction Pattern, checks if both volume and price are contracting
        volume_reduce_5d = [i for i in self.volume_reduce.get(size=5)]
        price_contract_5d = [i for i in self.price_contract.get(size=5)]
        cond_1 = any(
            v > 0.0 and p > 0.0 for v, p in zip(volume_reduce_5d, price_contract_5d)
        )

        # Condition 2: The current closing price must be the highest in the past 100 days
        # This indicates the indiv is reaching a new high
        cond_2 = self.data.close[0] == self.price_past_100_high[0]

        # Condition 3: The current volume must be greater than 80% of the 20-day average volume
        # This ensures there is sufficient trading activity
        cond_3 = self.data.volume[0] > self.vol_20_mean[0] * 0.8

        # Set the VCP line value to 1 if all conditions are met, otherwise set to -1
        self.lines.vcp[0] = 1 if cond_1 & cond_2 & cond_3 else -1
