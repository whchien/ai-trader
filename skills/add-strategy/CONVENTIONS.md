# Naming Conventions & Coding Standards

Established conventions and standards for creating trading strategies in the ai-trader framework.

## Table of Contents

1. [File Naming](#file-naming)
2. [Class Naming](#class-naming)
3. [Parameter Naming](#parameter-naming)
4. [Import Ordering](#import-ordering)
5. [BaseStrategy Inheritance](#basestrategy-inheritance)
6. [Docstring Format](#docstring-format)
7. [Code Structure](#code-structure)
8. [Indicator Usage](#indicator-usage)

---

## File Naming

### Convention

- **Format:** `lowercase_with_underscores.py`
- **Derived from:** PascalCase class name, converted to snake_case
- **Location:** `ai_trader/backtesting/strategies/{classic|portfolio}/`

### Examples

| Class Name | File Name | Location |
|------------|-----------|----------|
| `DoubleTopStrategy` | `double_top.py` | `strategies/classic/` |
| `BBandsStrategy` | `bbands.py` | `strategies/classic/` |
| `CrossSMAStrategy` | `sma.py` | `strategies/classic/` |
| `ROCRotationStrategy` | `roc_rotation.py` | `strategies/portfolio/` |
| `MACDBBandsStrategy` | `macd_bbands.py` | `strategies/classic/` |
| `TripleEMARotationStrategy` | `triple_ema_rotation.py` | `strategies/portfolio/` |

### Conversion Algorithm

```python
def class_to_filename(class_name: str) -> str:
    """Convert PascalCase class name to snake_case filename."""
    # Remove 'Strategy' suffix if present
    name = class_name.replace('Strategy', '')

    # Insert underscores before capital letters (excluding the first)
    result = []
    for i, char in enumerate(name):
        if char.isupper() and i > 0:
            result.append('_')
        result.append(char.lower())

    return ''.join(result) + '.py'

# Examples:
class_to_filename('BBandsStrategy')  # → 'bbands.py'
class_to_filename('DoubleTopStrategy')  # → 'double_top.py'
class_to_filename('ROCRotationStrategy')  # → 'roc_rotation.py'
```

---

## Class Naming

### Convention

- **Format:** `PascalCase` + `Strategy` suffix
- **Pattern:** `{Descriptor}{Strategy}`
- **Never:** Omit the `Strategy` suffix

### Examples

| Pattern | Examples |
|---------|----------|
| Single Indicator | `BBandsStrategy`, `MACDStrategy`, `RSIStrategy` |
| Compound Indicators | `MACDBBandsStrategy`, `RsiBollingerBandsStrategy` |
| Patterns | `DoubleTopStrategy`, `VCPStrategy` |
| Combinations | `HybridAlphaRSIStrategy` |
| Rotation/Multi-asset | `ROCRotationStrategy`, `TripleRSIRotationStrategy` |

### Naming Guidelines

- **Be descriptive:** Class name should indicate the strategy's core approach
- **Use indicator names:** If based on an indicator (MACD, RSI, etc.), include it
- **Compound logic:** For multi-indicator strategies, list main indicators in order
- **Avoid abbreviations:** Use full names except for well-known indicators (RSI, MACD, ROC, EMA, SMA)

### Examples of Good vs. Bad

| ✓ Good | ✗ Poor | Reason |
|--------|--------|--------|
| `MomentumStrategy` | `MomStrategy` | Avoid unnecessary abbreviations |
| `AdaptiveRSIStrategy` | `RSIAdaptive` | Pattern: {Descriptor}{Indicator}{Strategy} |
| `TripleRSIRotationStrategy` | `TripleRotation` | Name indicates use of Triple RSI |
| `RiskAverseStrategy` | `RAStrategy` | Spell out descriptive words |
| `BuyHoldStrategy` | `BHStrategy` | Clear and explicit |

---

## Parameter Naming

### Convention

- **Format:** `lowercase_with_underscores`
- **Scope:** Single strategy level (not global)
- **Types:** `int`, `float`, `bool` primarily

### Examples

```python
params = dict(
    # Standard names for common parameters
    period=20,              # Lookback period (most common)
    fast=12,                # Fast period (typically for MACD, stochastic)
    slow=26,                # Slow period
    signal=9,               # Signal line (MACD signal)

    # Bollinger Bands specific
    bb_period=20,           # Bollinger Bands period
    bb_dev=2,               # Number of standard deviations

    # RSI specific
    rsi_period=14,          # RSI period
    rsi_threshold=30,       # Overbought/oversold level

    # Time-based
    hold_days=30,           # Holding period in days
    look_back_period=60,    # Historical lookback

    # Momentum/selection
    top_k=5,                # Number of top assets to select
    min_roc=0.0,            # Minimum rate of change

    # Boolean flags
    use_filter=True,        # Whether to apply additional filter
    adaptive=False,         # Whether to use adaptive thresholds
)
```

### Parameter Naming Rules

1. **Descriptive:** Names should indicate what the parameter controls
2. **Abbreviated Indicator Names:** OK to use MACD, RSI, BB, ROC
   ```python
   macd_fast=12        # ✓ Good
   macd_f=12           # ✗ Avoid full abbreviation
   ```

3. **Consistency:** Use same names across similar strategies
   ```python
   # Across multiple strategies, 'period' means the same thing
   params = dict(period=20)  # ✓ Standard
   params = dict(lookback=20)  # ✗ Avoid variations
   ```

4. **Unit Clarity:** Include units when not obvious
   ```python
   hold_days=30        # ✓ Clear unit
   hold=30             # ✗ Unit unclear
   threshold_pct=2.5   # ✓ Percentage clear
   threshold=2.5       # ✗ Unclear
   ```

5. **No Python Keywords:** Never use reserved keywords
   ```python
   params = dict(period=20, class_name='test')  # ✗ Don't use 'class'
   params = dict(period=20)  # ✓ OK
   ```

---

## Import Ordering

### Convention

Import order follows Python PEP 8 with project-specific grouping:

1. **Standard library imports**
2. **Third-party imports** (backtrader)
3. **Project imports** (ai_trader modules)
4. **Custom indicator imports** (same as project imports, but explicit)

### Example

```python
# Standard library (if needed)
import datetime

# Third-party
import backtrader as bt

# Project imports - Base classes
from ai_trader.backtesting.strategies.base import BaseStrategy

# Project imports - Utilities
from ai_trader.core.logging import get_logger

# Custom indicators (if used)
from ai_trader.backtesting.strategies.indicators import DoubleTop, RSRS
```

### Complete Real-World Example

Classic strategy with custom indicators:
```python
"""
Module docstring here.
"""

import backtrader as bt

from ai_trader.backtesting.strategies.base import BaseStrategy
from ai_trader.backtesting.strategies.indicators import DoubleTop
```

Portfolio strategy (typically no custom indicators):
```python
"""
Module docstring here.
"""

import backtrader as bt

from ai_trader.backtesting.strategies.base import BaseStrategy
```

---

## BaseStrategy Inheritance

### Required: Call super().__init__()

All strategies MUST call `super().__init__()` in their `__init__` method:

```python
def __init__(self):
    """Initialize strategy indicators."""
    super().__init__()  # ← REQUIRED

    # Then initialize your indicators
    self.sma = bt.indicators.SMA(self.data)
```

### Why This Matters

The `BaseStrategy.__init__()` method (from base.py:15-27):
1. Initializes the parent `bt.Strategy` class
2. Logs all strategy parameters with their default values
3. Provides consistent logging infrastructure

Example output:
```
INFO: DoubleTopStrategy initialized with sma_short=60, sma_long=120, vol_short=5, vol_long=20, past_highest=60
```

### Using the Logging Infrastructure

After calling `super().__init__()`, you have access to:

**1. `self.log(text)` method:**
```python
self.log(f"Entered position at ${self.data.close[0]:.2f}")
```

Output:
```
INFO: 2023-01-15 │ Entered position at $150.23
```

**2. Automatic parameter logging:**
- Happens in BaseStrategy.__init__()
- All non-private, non-callable attributes are logged
- No manual logging needed

**3. Date-formatted messages:**
- `self.log()` automatically prepends ISO date from `self.datas[0].datetime.date(0)`
- Consistent format across all strategies

### Order Methods

`BaseStrategy` provides methods (inherited from `bt.Strategy`):

**Single-stock (classic):**
```python
self.buy()           # Buy at market (full order)
self.sell()          # Sell at market (full order)
self.close()         # Close entire position
self.order_target_size(size)     # Target specific size
self.order_target_percent(target) # Target percentage
```

**Multi-asset (portfolio):**
```python
self.order_target_percent(data, target=weight)  # Specify which asset
```

### Notification Methods (Already Implemented)

`BaseStrategy` provides pre-implemented notification methods:

**`notify_order(order)`** - Called when order status changes (base.py:36-90)
```python
# Already logs:
# - BUY/SELL executions with price, value, commission
# - Order failures with reason
# - No need to override unless special handling needed
```

**`notify_trade(trade)`** - Called when trade closes (base.py:92-108)
```python
# Already logs:
# - Closed trade P&L (gross and net)
# - No need to override unless special handling needed
```

**Don't override these unless you need custom behavior.**

---

## Docstring Format

### Module-Level Docstring

```python
"""
Strategy Name

Brief description (1-2 sentences) of what the strategy does and the market
conditions it targets or problems it solves.
"""
```

Example:
```python
"""
Double Top Pattern Strategy

Detects double top reversal patterns and implements mean reversion trades
with time-based and signal-based exit conditions.
"""
```

### Class-Level Docstring

```python
class StrategyNameStrategy(BaseStrategy):
    """
    Strategy Name - One-line tagline describing the core approach.

    Detailed description paragraph (3-4 sentences) explaining:
    - The trading logic and how it works
    - Market conditions or price patterns it identifies
    - Why this approach is effective in those conditions
    - Any special characteristics or risks

    Entry Logic (Buy):
    - Condition 1 description
    - Condition 2 description
    - [Optional: Condition 3]

    Exit Logic (Sell):
    - Condition 1 description
    - Condition 2 description
    - [Optional: Condition 3]

    Parameters:
    - param_name (type): Description [default: value]
    - another_param (int): Description [default: value]

    Notes:
    - Implementation detail or insight 1
    - Implementation detail or insight 2
    - [Optional: Consideration 3]
    """
```

### Real Example

```python
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
```

### Docstring Sections Explained

1. **One-line tagline:** Immediately communicates the core idea
   - "Mean reversion after double top formation"
   - "Dynamic momentum-based multi-asset rotation"

2. **Detailed description:** 3-4 sentences explaining the strategy
   - What pattern/condition it identifies
   - How it uses indicators to confirm
   - Why it works

3. **Entry Logic (Buy):** Bullet points for each entry condition
   - What signals trigger a buy?
   - What confluence is needed?
   - What indicator values/relationships?

4. **Exit Logic (Sell):** Bullet points for each exit condition
   - What signals trigger a sell?
   - Time-based exits?
   - Signal reversals?

5. **Parameters:** One line per parameter
   - Format: `- name (type): Description [default: value]`
   - Include what the parameter controls
   - Always include default value

6. **Notes:** Implementation insights or considerations
   - Why certain design choices were made
   - Conditions under which the strategy works well
   - Potential limitations or edge cases

---

## Code Structure

### Classic Strategy Template

```python
"""Module docstring."""

import backtrader as bt

from ai_trader.backtesting.strategies.base import BaseStrategy
# from ai_trader.backtesting.strategies.indicators import CustomIndicator


class StrategyNameStrategy(BaseStrategy):
    """Class docstring with Entry/Exit/Parameters/Notes."""

    params = dict(param1=default1, param2=default2)

    def __init__(self):
        """Initialize indicators and signals."""
        super().__init__()
        # Initialize indicators
        # Create signal lines if helpful

    def next(self):
        """Execute trading logic."""
        if self.position.size == 0:
            # Entry logic
            if self.buy_signal[0]:
                self.buy()
        else:
            # Exit logic
            if self.exit_signal[0]:
                self.close()


if __name__ == "__main__":
    from ai_trader.utils.backtest import run_backtest

    results = run_backtest(
        strategy=StrategyNameStrategy,
        data_source=None,
        cash=1000000,
        commission=0.001425,
    )

    print("Backtest completed! Use cerebro.plot() to visualize results.")
```

### Portfolio Strategy Template

```python
"""Module docstring."""

import backtrader as bt

from ai_trader.backtesting.strategies.base import BaseStrategy


class StrategyNameStrategy(BaseStrategy):
    """Class docstring with Entry/Exit/Parameters/Notes."""

    params = dict(param1=default1, top_k=5)

    def __init__(self):
        """Initialize indicators for all assets."""
        super().__init__()
        self.indicators = {
            data: bt.ind.CustomIndicator(data, period=self.params.param1)
            for data in self.datas
        }
        self.top_k = self.params.top_k

    def next(self):
        """Execute portfolio rebalancing logic."""
        # 1. Get current holdings
        holding = [d for d, pos in self.getpositions().items() if pos]

        # 2. Identify candidates and exits
        to_buy = [data for data in self.datas if self._is_buy_signal(data)]
        to_close = [data for data in self.datas if self._is_exit_signal(data)]

        # 3. Close exits
        for data in to_close:
            if data in holding:
                self.order_target_percent(data, target=0.0)
                self.log(f"Exit {data._name}")

        # 4. Build and rank portfolio
        portfolio = list(set(to_buy + holding))
        if not portfolio:
            return

        if len(portfolio) > self.top_k:
            ranked = sorted(
                [(d, self.indicators[d][0]) for d in portfolio],
                key=lambda x: x[1],
                reverse=True,
            )
            portfolio = [d for d, _ in ranked[:self.top_k]]

        # 5. Allocate positions
        weight = 1.0 / len(portfolio)
        for data in portfolio:
            self.order_target_percent(data, target=weight * 0.95)

    def _is_buy_signal(self, data):
        """Check if asset meets buy criteria."""
        return False

    def _is_exit_signal(self, data):
        """Check if asset meets exit criteria."""
        return False


if __name__ == "__main__":
    from ai_trader.utils.backtest import run_backtest

    results = run_backtest(
        strategy=StrategyNameStrategy,
        data_source=None,
        cash=1000000,
        commission=0.001425,
    )

    print("Backtest completed! Use cerebro.plot() to visualize results.")
```

---

## Indicator Usage

### Standard Indicators (Use `bt.ind.*`)

For well-known technical indicators, use backtrader's built-in implementations:

```python
# Moving Averages
self.sma = bt.indicators.SMA(self.data, period=20)
self.ema = bt.indicators.EMA(self.data, period=12)

# Momentum Indicators
self.macd = bt.indicators.MACD(self.data, period1=12, period2=26, period3=9)
self.rsi = bt.indicators.RSI(self.data, period=14)
self.roc = bt.indicators.RateOfChange(self.data, period=20)
self.stoch = bt.indicators.Stochastic(self.data)

# Volatility Indicators
self.bb = bt.indicators.BollingerBands(self.data, period=20, devfactor=2)
self.atr = bt.indicators.ATR(self.data, period=14)

# Other
self.highest = bt.indicators.Highest(self.data.close, period=20)
self.lowest = bt.indicators.Lowest(self.data.close, period=20)
```

### Custom Indicators (From `indicators.py`)

For indicators specific to ai-trader, import from the indicators module:

```python
from ai_trader.backtesting.strategies.indicators import (
    DoubleTop,
    RSRS,
    NormRSRS,
    RecentHigh,
    TripleRSI,
)

# Usage in __init__
self.double_top = DoubleTop(
    self.data,
    sma_short=self.params.sma_short,
    sma_long=self.params.sma_long,
    vol_short=self.params.vol_short,
    vol_long=self.params.vol_long,
    past_highest=self.params.past_highest,
)
```

### Accessing Indicator Lines

Backtrader indicators expose lines (price streams) that can be indexed:

```python
# Current value (bar 0)
current_value = indicator[0]

# Previous bar
previous_value = indicator[-1]  # or indicator[1]

# Named lines (if available)
bb = bt.indicators.BollingerBands(self.data)
mid_band = bb.lines.mid[0]
upper_band = bb.lines.top[0]
lower_band = bb.lines.bot[0]

# MACD example
macd = bt.indicators.MACD(self.data)
macd_line = macd.lines.macd[0]
signal_line = macd.lines.signal[0]
histogram = macd.lines.histogram[0]
```

### Pre-Computing Signal Lines

For clarity, compute signal lines in `__init__`:

```python
def __init__(self):
    super().__init__()
    self.sma_short = bt.indicators.SMA(self.data, period=20)
    self.sma_long = bt.indicators.SMA(self.data, period=50)

    # Pre-compute signals for cleaner next()
    self.buy_signal = self.sma_short > self.sma_long
    self.sell_signal = self.sma_short < self.sma_long
```

Then use in `next()`:
```python
def next(self):
    if self.buy_signal[0]:
        self.buy()
```

---

## Quick Checklist

- [ ] Class name ends with `Strategy`
- [ ] Filename is snake_case (derived from class name)
- [ ] Module docstring present
- [ ] Class docstring includes Entry/Exit/Parameters/Notes
- [ ] `super().__init__()` called in `__init__`
- [ ] All parameters have default values
- [ ] Imports ordered: stdlib → backtrader → project → indicators
- [ ] Custom indicators exist in `indicators.py` (if used)
- [ ] `next()` method implements trading logic
- [ ] `__main__` block has backtest scaffolding
- [ ] Strategy is registered in appropriate `__init__.py`

---

Generated with Claude Code