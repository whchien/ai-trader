# Reference Patterns & Examples

Complete code examples from the ai-trader codebase demonstrating established patterns for strategy creation.

## Table of Contents

1. [Classic Strategy - DoubleTopStrategy](#doubletopstrategy)
2. [Classic Strategy - BBandsStrategy](#bbandsStrategy)
3. [Portfolio Strategy - ROCRotationStrategy](#rocrotationstrategy)

---

## DoubleTopStrategy

**Location:** `ai_trader/backtesting/strategies/classic/double_top.py`

**Pattern Highlights:**
- Custom indicator usage (DoubleTop from indicators.py)
- Time-based exit condition with date tracking
- Signal-based logic (indicator line > 0)
- Comprehensive docstring with Entry/Exit/Parameters/Notes

```python
"""
Double Top Pattern Strategy

Detects double top reversal patterns and implements mean reversion trades
with time-based and signal-based exit conditions.
"""

import backtrader as bt

from ai_trader.backtesting.strategies.base import BaseStrategy
from ai_trader.backtesting.strategies.indicators import DoubleTop


class DoubleTopStrategy(BaseStrategy):
    """
    Double Top Pattern Strategy - Mean reversion after double top formation.

    Identifies double top reversal patterns where price fails to break above a
    recent high twice, signaling potential downside reversal. Uses trend and
    volatility analysis to confirm pattern validity.

    Entry Logic (Buy):
    - Double Top indicator signal > 0 (pattern confirmed and price consolidated)

    Exit Logic (Sell):
    - Position held for maximum 30 days, or
    - Double Top indicator signal turns negative (pattern invalidated)

    Parameters:
    - sma_short (int): Short-term SMA period for trend analysis [default: 60]
    - sma_long (int): Long-term SMA period for trend analysis [default: 120]
    - vol_short (int): Short-term volatility period [default: 5]
    - vol_long (int): Long-term volatility period [default: 20]
    - past_highest (int): Lookback period for identifying recent highs [default: 60]

    Notes:
    - Time-based exit prevents position from staying open indefinitely
    - Requires confirmation from volatility and trend indicators
    - Double top is a reversal pattern; trades against the prior uptrend
    """

    params = dict(sma_short=60, sma_long=120, vol_short=5, vol_long=20, past_highest=60)

    def __init__(self):
        """Initialize Double Top pattern detector with trend and volatility parameters."""
        super().__init__()  # ← Call super().__init__() to enable parameter logging
        self.double_top = DoubleTop(
            self.data,
            sma_short=self.params.sma_short,
            sma_long=self.params.sma_long,
            vol_short=self.params.vol_short,
            vol_long=self.params.vol_long,
            past_highest=self.params.past_highest,
        )
        self.entry_date = None  # ← Track entry date for time-based exit

        # Create signal line for easy reference in next()
        self.buy_signal = self.double_top.signal > 0

    def next(self):
        """Execute trading logic: enter on pattern signal, exit on time or signal reversal."""
        if self.position.size == 0:
            # No position: check for entry signal
            if self.buy_signal[0]:
                self.buy()
                self.entry_date = self.datetime.date(ago=0)

        else:
            # Have position: check for exit conditions
            holding_period = (self.datetime.date(ago=0) - self.entry_date).days

            # Close position after 30 days or if signal turns negative
            if holding_period > 30 or self.double_top.signal[0] < 0:
                self.close()
                self.entry_date = None


if __name__ == "__main__":
    from ai_trader.utils.backtest import run_backtest

    # Run backtest with DoubleTopStrategy
    results = run_backtest(
        strategy=DoubleTopStrategy,
        data_source=None,  # Use example data
        cash=1000000,
        commission=0.001425,
    )

    print("Backtest completed! Use cerebro.plot() to visualize results.")
```

**Key Patterns to Note:**

1. **Custom Indicator Import:** Line 8-9
   ```python
   from ai_trader.backtesting.strategies.indicators import DoubleTop
   ```

2. **super().__init__() Call:** Line 43
   - Enables automatic parameter logging in BaseStrategy
   - Must be called even though parent's __init__ is empty

3. **Parameter Definition:** Line 40
   ```python
   params = dict(sma_short=60, sma_long=120, vol_short=5, vol_long=20, past_highest=60)
   ```
   - All parameters have default values
   - Use lowercase with underscores

4. **Signal Line Creation:** Line 54
   ```python
   self.buy_signal = self.double_top.signal > 0
   ```
   - Pre-compute signals in __init__ for cleaner next() logic

5. **Time-Based Exit:** Lines 62-63
   ```python
   holding_period = (self.datetime.date(ago=0) - self.entry_date).days
   if holding_period > 30 or self.double_top.signal[0] < 0:
   ```

---

## BBandsStrategy

**Location:** `ai_trader/backtesting/strategies/classic/bbands.py`

**Pattern Highlights:**
- Simple mean reversion logic
- Backtrader standard indicator (BollingerBands)
- Minimal parameters
- Clear, straightforward trading logic

```python
"""
Bollinger Bands Strategy

Implements a mean reversion strategy using Bollinger Bands to identify
overbought and oversold conditions based on price volatility.
"""

import backtrader as bt

from ai_trader.backtesting.strategies.base import BaseStrategy


class BBandsStrategy(BaseStrategy):
    """
    Bollinger Bands Strategy - Mean reversion based on volatility bands.

    Uses Bollinger Bands to identify potential entry and exit points based on
    the principle that prices tend to return to the mean after reaching extreme
    levels defined by standard deviation bands.

    Entry Logic (Buy):
    - Close price falls below the lower Bollinger Band (oversold condition)

    Exit Logic (Sell):
    - Close price rises above the upper Bollinger Band (overbought condition)

    Parameters:
    - period (int): Number of periods for moving average calculation [default: 20]
    - devfactor (float): Number of standard deviations for band width [default: 2]

    Notes:
    - Works best in ranging/consolidating markets; may generate false signals in strong trends
    - Standard devfactor of 2 captures approximately 95% of price action
    - Mean reversion strategies are counter-trend in nature
    """

    params = dict(period=20, devfactor=2)

    def __init__(self):
        """Initialize Bollinger Bands indicator with configured period and deviation factor."""
        super().__init__()  # ← Important: call super().__init__()
        self.bb = bt.indicators.BollingerBands(
            self.data, period=self.params.period, devfactor=self.params.devfactor
        )

    def next(self):
        """Execute trading logic based on price position relative to Bollinger Bands."""
        signal_buy = self.data.close[0] < self.bb.lines.bot[0]
        signal_sell = self.data.close[0] > self.bb.lines.top[0]

        if self.position.size == 0:
            if signal_buy:
                self.buy()

        if self.position.size > 0:
            if signal_sell:
                self.close()


if __name__ == "__main__":
    from ai_trader.utils.backtest import run_backtest

    # Run backtest with Bollinger Bands strategy
    results = run_backtest(
        strategy=BBandsStrategy,
        data_source=None,  # Use example data
        cash=1000000,
        commission=0.001425,
        strategy_params={"period": 20, "devfactor": 2.0},
    )

    print("\nBacktest completed! Use cerebro.plot() to visualize results.")
```

**Key Patterns to Note:**

1. **Backtrader Standard Indicator:** Line 42
   ```python
   self.bb = bt.indicators.BollingerBands(self.data, period=..., devfactor=...)
   ```
   - Use `bt.indicators.*` for standard indicators
   - Access lines via `self.bb.lines.bot[0]`, `self.bb.lines.top[0]`

2. **Simple Signal Logic:** Lines 47-48
   ```python
   signal_buy = self.data.close[0] < self.bb.lines.bot[0]
   signal_sell = self.data.close[0] > self.bb.lines.top[0]
   ```
   - Compute signals inline if simple

3. **Minimal Parameter Set:** Line 37
   ```python
   params = dict(period=20, devfactor=2)
   ```
   - Only parameters that strategy creators might want to tune

4. **Clean next() Logic:** Lines 50-56
   - First check: if no position and buy signal → buy
   - Second check: if position and sell signal → close
   - This pattern applies to most simple strategies

---

## ROCRotationStrategy

**Location:** `ai_trader/backtesting/strategies/portfolio/roc_rotation.py`

**Pattern Highlights:**
- Multi-asset portfolio strategy
- Dynamic ranking and selection
- Equal-weight allocation
- Portfolio rotation based on momentum

```python
"""
Rate of Change (ROC) Rotation Strategy

Multi-asset portfolio strategy that rotates capital to assets with
the strongest positive momentum, concentrating positions in top-k assets.
"""

import backtrader as bt

from ai_trader.backtesting.strategies.base import BaseStrategy


class ROCRotationStrategy(BaseStrategy):
    """
    ROC Rotation Strategy - Dynamic momentum-based multi-asset rotation.

    A portfolio strategy that applies Rate of Change analysis to multiple assets
    and rotates capital to the top-k assets with strongest momentum (highest ROC).
    Exits positions in assets with negative momentum. Equal-weight allocates
    portfolio among selected assets.

    Entry Logic (Buy):
    - Asset ROC > 0 (positive momentum)
    - Asset ranked in top-k by ROC value (highest momentum)

    Exit Logic (Sell):
    - Asset ROC < 0 (momentum reversal)
    - Position closed and capital reallocated to better opportunities

    Parameters:
    - period (int): Period for ROC calculation [default: 20]
    - top_k (int): Number of top assets to hold (internal, hard-coded to 5)

    Notes:
    - Rotates portfolio monthly or whenever momentum leaders change
    - Concentrates in top-5 assets to optimize risk-adjusted returns
    - Equal-weight allocation across selected assets (95% of capital, 5% buffer)
    - Positive momentum indicates accelerating price movements
    - ROC > 0 shows gains over the past period; < 0 shows losses
    """

    params = dict(period=20)

    def __init__(self):
        """Initialize Rate of Change indicators for all assets in the portfolio."""
        super().__init__()
        # ← Use self.datas to create indicator for EACH asset
        self.indicators = {
            data: bt.ind.RateOfChange(data, period=self.params.period) for data in self.datas
        }

        self.top_k = 5  # ← Hard-coded top-k (could be parameterized)

    def next(self):
        """Execute portfolio rebalancing: exit negative momentum, rotate to top-k momentum leaders."""
        # 1. Identify current holdings and candidates
        holding = [d for d, pos in self.getpositions().items() if pos]  # ← Get positions for all assets
        to_buy = [data for data, roc in self.indicators.items() if roc[0] > 0.0]  # ← Assets with positive momentum
        to_close = [data for data, roc in self.indicators.items() if roc[0] < 0.0]  # ← Assets to exit

        # 2. Close positions with negative momentum
        for data in to_close:
            if data in holding:
                self.order_target_percent(data=data, target=0.0)  # ← Exit completely
                self.log(f"Leave {data._name}")
                holding.remove(data)

        # 3. Build portfolio from buy signals + existing holdings
        portfolio = list(set(to_buy + holding))

        if not portfolio:  # Safety check: if no stocks selected, return
            return

        # 4. Select top-k by current indicator value
        if len(portfolio) > self.top_k:
            # Rank candidates by indicator value
            data_roc = {item: self.indicators[item][0] for item in portfolio}
            portfolio = sorted(
                data_roc.items(),  # (data, roc_value) tuples
                key=lambda x: x[1],
                reverse=True,  # Highest ROC first
            )
            portfolio = [item[0] for item in portfolio[: self.top_k]]  # Extract data objects
            self.log(f"Selected portfolio: {[p._name for p in portfolio]}")

        # 5. Equal-weight allocation across selected assets
        weight = 1 / len(portfolio)
        for p in portfolio:
            if p in holding:
                # Already holding: rebalance to target weight
                self.log(f"Rebalance {p._name}")
                self.order_target_percent(p, target=weight * 0.95)
            else:
                # New position: enter
                self.log(f"Enter {p._name}")
                self.order_target_percent(p, target=weight * 0.95)


if __name__ == "__main__":
    from ai_trader.utils.backtest import run_backtest

    # Run backtest with ROCRotationStrategy
    results = run_backtest(
        strategy=ROCRotationStrategy,
        data_source=None,  # Use example data
        cash=1000000,
        commission=0.001425,
    )

    print("Backtest completed! Use cerebro.plot() to visualize results.")
```

**Key Patterns to Note:**

1. **Multi-Asset Indicator Setup:** Lines 49-51
   ```python
   self.indicators = {
       data: bt.ind.RateOfChange(data, period=self.params.period) for data in self.datas
   }
   ```
   - Use `self.datas` to iterate over all assets
   - Store indicators in a dictionary keyed by data

2. **Position Lookup:** Line 58
   ```python
   holding = [d for d, pos in self.getpositions().items() if pos]
   ```
   - `self.getpositions()` returns dict of {data: position_object}
   - Filter for assets with non-zero position

3. **Signal Generation:** Lines 59-60
   ```python
   to_buy = [data for data, roc in self.indicators.items() if roc[0] > 0.0]
   to_close = [data for data, roc in self.indicators.items() if roc[0] < 0.0]
   ```
   - Iterate over indicators dict to find candidates

4. **Position Management:** Line 65
   ```python
   self.order_target_percent(data=data, target=0.0)
   ```
   - `order_target_percent()` is the multi-asset way to size positions
   - `target=0.0` closes the position completely
   - `target=0.95/N` allocates equal weight with 5% cash buffer

5. **Ranking & Selection:** Lines 73-79
   ```python
   data_roc = {item: self.indicators[item][0] for item in portfolio}
   portfolio = sorted(
       data_roc.items(),
       key=lambda x: x[1],
       reverse=True,
   )
   portfolio = [item[0] for item in portfolio[: self.top_k]]
   ```
   - Extract indicator values, rank by value, select top-k

6. **Dynamic Allocation:** Lines 85-91
   ```python
   weight = 1 / len(portfolio)
   for p in portfolio:
       if p in holding:
           self.order_target_percent(p, target=weight * 0.95)
       else:
           self.order_target_percent(p, target=weight * 0.95)
   ```
   - Equal-weight: divide portfolio by number of selected assets
   - 0.95 multiplier leaves 5% cash buffer
   - Use same code for rebalancing and entry (idempotent)

---

## Summary of Patterns

### Classic Strategy Pattern
```python
# 1. Module docstring + imports
# 2. Class inherits from BaseStrategy
# 3. params = dict(...)
# 4. def __init__(self): super().__init__() + indicators
# 5. def next(self): if self.position.size == 0: buy else: close
# 6. if __name__ == "__main__": run_backtest(...)
```

### Portfolio Strategy Pattern
```python
# 1. Module docstring + imports
# 2. Class inherits from BaseStrategy
# 3. params = dict(...)
# 4. def __init__(self): super().__init__() + self.indicators = {data: ind for data in self.datas}
# 5. def next(self):
#    - holding = [d for d, pos in self.getpositions().items() if pos]
#    - to_buy = [data for data in self.datas if signal]
#    - to_close = [data for data in self.datas if exit_signal]
#    - close positions: self.order_target_percent(data, target=0.0)
#    - rank and select top-k
#    - allocate: self.order_target_percent(data, target=weight*0.95)
# 6. if __name__ == "__main__": run_backtest(...)
```

### Docstring Pattern
```python
class StrategyName(BaseStrategy):
    """
    Strategy Name - One-liner tagline.

    Multi-line detailed description explaining:
    - What the strategy does
    - Market conditions it targets
    - Why it works

    Entry Logic (Buy):
    - Bullet 1
    - Bullet 2

    Exit Logic (Sell):
    - Bullet 1
    - Bullet 2

    Parameters:
    - name (type): description [default: value]

    Notes:
    - Implementation insight
    - Another insight
    """
```

---

Generated with Claude Code
