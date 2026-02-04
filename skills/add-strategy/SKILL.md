---
name: add-strategy
description: Create a new trading strategy for the ai-trader backtesting framework. Handles file creation, registration, docstrings, and backtest scaffolding.
disable-model-invocation: true
argument-hint: "[strategy-type: classic|portfolio]"
allowed-tools: "Read, Write, Edit, Glob, Grep, Bash"
---

# add-strategy Skill

Create a new trading strategy for the ai-trader backtesting framework with automatic file generation, registration, and validation.

## Overview

This skill automates the creation of trading strategies following established patterns in the ai-trader project. It handles:

- File creation with proper naming conventions (PascalCase class → snake_case filename)
- Comprehensive docstrings (module and class level)
- Parameter validation and defaults
- Automatic registration in `__init__.py` files
- Standalone backtest scaffolding
- Pre-flight validation for name conflicts and custom indicators

Two strategy types are supported:

- **Classic**: Single-stock strategies (e.g., DoubleTopStrategy, BBandsStrategy)
- **Portfolio**: Multi-asset rotation strategies (e.g., ROCRotationStrategy, MultiBBandsRotationStrategy)

## Interactive Workflow

The skill guides you through the following steps:

### Step 1: Strategy Type
Confirm whether this is a classic (single-stock) or portfolio (multi-asset) strategy.

### Step 2: Name & Description
- Provide the strategy name in PascalCase (e.g., "MACDBBands")
- Provide a 1-2 sentence description
- The skill automatically converts to snake_case for the filename (macd_bbands.py)

### Step 3: Parameters
Define parameters as comma-separated `name=value` pairs:
- Example: `fast=12, slow=26, signal=9, bb_period=20`
- All parameters must have default values
- Parameter names must be valid Python identifiers

### Step 4: Entry & Exit Logic
- Describe the entry condition (buy signal)
- Describe the exit condition (sell signal)
- For portfolio strategies, describe rotation/rebalancing logic

### Step 5: Custom Indicators (Optional)
If your strategy uses custom indicators from `indicators.py`, list them:
- Available: DoubleTop, RSRS, NormRSRS, RecentHigh, TripleRSI, etc.
- The skill verifies they exist and generates the import statement

### Step 6: Preview & Confirmation
Review the generated file structure before creation:
- Target file path
- Class name and type
- Parameters
- Files to be modified (__init__.py imports and __all__)

### Step 7: Creation & Verification
The skill creates:
- Strategy file with complete structure
- Updates imports and __all__ list in __init__.py
- Validates syntax by attempting import
- Shows git status for verification

## Usage Examples

### Creating a Classic Strategy

```bash
$ /add-strategy classic

Creating a classic single-stock strategy.

What should we name this strategy? (e.g., "BollingerBreakout")
> MACDBBands

Brief description (1-2 sentences)?
> Combines MACD for trend and Bollinger Bands for entry timing

Parameters with defaults? (e.g., "fast=12, slow=26, signal=9, bb_period=20")
> fast=12, slow=26, signal=9, bb_period=20, bb_dev=2

Entry condition (buy signal)?
> MACD crosses above signal line AND price below lower Bollinger Band

Exit condition (sell signal)?
> MACD crosses below signal line OR price above upper Bollinger Band

Any custom indicators from indicators.py? (e.g., DoubleTop, RSRS)
> No

[Preview shown]

Proceed with creation? (yes/no)
> yes

✓ Created macd_bbands.py
✓ Updated classic/__init__.py (added import)
✓ Updated classic/__init__.py (added to __all__)
✓ Verified file is importable

Next steps:
1. Test standalone: python ai_trader/backtesting/strategies/classic/macd_bbands.py
2. Review generated code and refine logic
3. Test via CLI: ai-trader quick MACDBBandsStrategy your_data.csv
4. Check changes: git diff
5. Commit when ready
```

### Creating a Portfolio Strategy

```bash
$ /add-strategy portfolio

Creating a portfolio multi-asset strategy.

What should we name this strategy? (e.g., "MomentumRotation")
> TripleEMARotation

Brief description?
> Rotates portfolio to assets with strongest triple EMA alignment

Parameters?
> short_ema=10, med_ema=20, long_ema=50, top_k=5

Rotation/Rebalancing logic?
> Rotate monthly to top-5 assets where all three EMAs are bullishly aligned

Custom indicators?
> No

[Preview shown]

Proceed with creation? (yes/no)
> yes

✓ Created triple_ema_rotation.py
✓ Updated portfolio/__init__.py (added import)
✓ Updated portfolio/__init__.py (added to __all__)
✓ Verified file is importable
```

## File Templates

### Classic Strategy Template

```python
"""
[Strategy Name]

[1-2 sentence description of what the strategy does and the market conditions it targets.]
"""

import backtrader as bt

from ai_trader.backtesting.strategies.base import BaseStrategy
# [Add custom indicator imports if needed]
# from ai_trader.backtesting.strategies.indicators import CustomIndicator


class [StrategyName]Strategy(BaseStrategy):
    """
    [Strategy Name] - [One-line tagline describing the core approach].

    [Detailed description paragraph explaining the trading logic, market conditions,
    and why this strategy works in those conditions.]

    Entry Logic (Buy):
    - Condition 1
    - Condition 2

    Exit Logic (Sell):
    - Condition 1
    - Condition 2

    Parameters:
    - param_name (type): Description [default: value]

    Notes:
    - Insight 1
    - Insight 2
    """

    params = dict(param1=value1, param2=value2)

    def __init__(self):
        """Initialize indicators and signals."""
        super().__init__()
        # Initialize indicators here
        # self.indicator = bt.indicators.SMA(self.data)

    def next(self):
        """Execute trading logic each bar."""
        if self.position.size == 0:
            # Check buy signal and enter
            pass
        else:
            # Check exit signal and close
            pass


if __name__ == "__main__":
    from ai_trader.utils.backtest import run_backtest

    # Run backtest with [StrategyName]Strategy
    results = run_backtest(
        strategy=[StrategyName]Strategy,
        data_source=None,  # Use example data
        cash=1000000,
        commission=0.001425,
    )

    print("Backtest completed! Use cerebro.plot() to visualize results.")
```

### Portfolio Strategy Template

```python
"""
[Strategy Name]

[1-2 sentence description of the portfolio rotation strategy.]
"""

import backtrader as bt

from ai_trader.backtesting.strategies.base import BaseStrategy
# [Add custom indicator imports if needed]


class [StrategyName]Strategy(BaseStrategy):
    """
    [Strategy Name] - [One-line tagline].

    [Detailed description of the rotation/rebalancing logic.]

    Entry Logic (Buy):
    - Condition 1 (applies to each asset in the portfolio)
    - Condition 2

    Exit Logic (Sell):
    - Condition 1
    - Asset no longer in top-k performers

    Parameters:
    - param_name (type): Description [default: value]

    Notes:
    - Rotates portfolio based on selection criteria
    - Equal-weight or custom allocation across selected assets
    - Rebalances when conditions change
    """

    params = dict(param1=value1, top_k=5)

    def __init__(self):
        """Initialize indicators for all assets."""
        super().__init__()
        self.indicators = {
            data: bt.ind.SMA(data) for data in self.datas
        }
        self.top_k = self.params.top_k

    def next(self):
        """Execute portfolio rebalancing logic."""
        # Get current holdings
        holding = [d for d, pos in self.getpositions().items() if pos]

        # Identify candidates and exits
        to_buy = [data for data in self.datas if self._is_buy_signal(data)]
        to_close = [data for data in self.datas if self._is_exit_signal(data)]

        # Close positions in assets with exit signals
        for data in to_close:
            if data in holding:
                self.order_target_percent(data=data, target=0.0)
                self.log(f"Exit {data._name}")

        # Select top-k by performance
        portfolio = list(set(to_buy + holding))
        if not portfolio:
            return

        if len(portfolio) > self.top_k:
            # Rank by indicator and select top-k
            ranked = sorted(
                [(d, self.indicators[d][0]) for d in portfolio],
                key=lambda x: x[1],
                reverse=True,
            )
            portfolio = [d for d, _ in ranked[:self.top_k]]

        # Equal-weight allocation
        weight = 1 / len(portfolio)
        for data in portfolio:
            self.order_target_percent(data, target=weight * 0.95)

    def _is_buy_signal(self, data):
        """Check if data meets buy criteria."""
        # Implement your entry logic
        return False

    def _is_exit_signal(self, data):
        """Check if data meets exit criteria."""
        # Implement your exit logic
        return False


if __name__ == "__main__":
    from ai_trader.utils.backtest import run_backtest

    # Run backtest with [StrategyName]Strategy
    results = run_backtest(
        strategy=[StrategyName]Strategy,
        data_source=None,  # Use example data
        cash=1000000,
        commission=0.001425,
    )

    print("Backtest completed! Use cerebro.plot() to visualize results.")
```

## Registration Logic

When creating a strategy, the skill updates the appropriate `__init__.py` file:

**Example for classic/macd_bbands.py:**

```python
# Before
from ai_trader.backtesting.strategies.classic.bbands import BBandsStrategy
from ai_trader.backtesting.strategies.classic.double_top import DoubleTopStrategy

__all__ = [
    "BBandsStrategy",
    "DoubleTopStrategy",
    # ...
]

# After
from ai_trader.backtesting.strategies.classic.bbands import BBandsStrategy
from ai_trader.backtesting.strategies.classic.double_top import DoubleTopStrategy
from ai_trader.backtesting.strategies.classic.macd_bbands import MACDBBandsStrategy

__all__ = [
    "BBandsStrategy",
    "DoubleTopStrategy",
    "MACDBBandsStrategy",
    # ...
]
```

**Key points:**
- Imports are added in alphabetical order by filename
- `__all__` list is maintained in alphabetical order
- Existing structure and formatting are preserved

## Validation

### Pre-Creation Checks

1. **Name Validation:**
   - Class name must be PascalCase (e.g., MACDBBands)
   - Converts to snake_case for filename (macd_bbands.py)
   - No file exists at target path
   - Class name not already in `__all__`

2. **Type Validation:**
   - Strategy type is "classic" or "portfolio"
   - Target directory exists

3. **Parameter Validation:**
   - All parameters have default values
   - Parameter names are valid Python identifiers
   - No reserved Python keywords as parameter names

4. **Indicator Validation:**
   - If custom indicators mentioned, verify they exist in indicators.py
   - Generate correct import statements

### Post-Creation Verification

1. File created successfully
2. Imports added to `__init__.py`
3. Name added to `__all__` list in correct position
4. File is syntactically valid (test import)
5. Git recognizes new/modified files

## Next Steps After Creation

1. **Review Generated Code:**
   - The generated template provides the structure; you'll add the specific trading logic
   - Implement `next()` method with your trading signals
   - For portfolio strategies, implement `_is_buy_signal()` and `_is_exit_signal()`

2. **Test Standalone:**
   ```bash
   python ai_trader/backtesting/strategies/classic/your_strategy.py
   ```

3. **Refine Parameters:**
   - Update default values based on backtesting results
   - Add parameter optimization later if needed

4. **Integration Testing:**
   ```bash
   ai-trader quick YourStrategyName your_data.csv
   ```

5. **Commit Changes:**
   ```bash
   git add ai_trader/backtesting/strategies/classic/your_strategy.py
   git add ai_trader/backtesting/strategies/classic/__init__.py
   git commit -m "Add YourStrategyName strategy"
   ```

## Related Documentation

- **PATTERNS.md** - Complete examples of implemented strategies with annotations
- **CONVENTIONS.md** - Naming rules, import ordering, parameter format, docstring structure
- **VALIDATION.md** - Detailed validation rules and error handling

## Tips & Best Practices

- **Inherit from BaseStrategy:** Always inherit from BaseStrategy, not directly from bt.Strategy
  - Provides automatic parameter logging via `__init__()`
  - Provides `self.log()` for consistent date-formatted logging
  - Provides `notify_order()` and `notify_trade()` implementations

- **Use Backtrader Indicators:** Use `bt.ind.*` for standard indicators (SMA, EMA, Bollinger Bands, MACD, RSI, etc.)

- **Custom Indicators:** Only create custom indicators if they're not available in backtrader
  - Check `indicators.py` first
  - Custom indicators should be reusable across multiple strategies

- **Parameter Naming:** Use descriptive, lowercase names with underscores
  - Good: `sma_short`, `bb_period`, `rsi_threshold`
  - Avoid: `x`, `n`, `val`

- **Docstrings:** Comprehensive docstrings help future maintenance
  - Module level: Brief purpose and what the strategy does
  - Class level: Entry/Exit/Parameters/Notes sections
  - Helps other developers understand your strategy at a glance

- **Testing:** Always test with the `__main__` block before committing
  - Ensures the strategy initializes correctly
  - Catches syntax errors early

- **Portfolio Strategies:** Use `self.datas` to iterate over all assets
  - Use `self.getpositions()` to check current holdings
  - Use `self.order_target_percent()` for position sizing
  - Rebalance systematically (monthly, when signals change, etc.)

## Error Messages & Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `File already exists` | A strategy with that name already exists | Choose a different name |
| `Class name already in __all__` | Name conflict in registration | Check existing strategies |
| `Invalid parameter name` | Parameter name is not a valid Python identifier | Use alphanumeric + underscores only |
| `Custom indicator not found` | Indicator doesn't exist in indicators.py | Use standard backtrader indicators or create a custom one |
| `Import failed` | Syntax error in generated file | Review the generated code and fix issues |

---

Generated with Claude Code
