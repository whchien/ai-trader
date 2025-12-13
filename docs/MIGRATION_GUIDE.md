# Migration Guide: From AITrader to Utility Functions

This guide helps you migrate from the deprecated `AITrader` wrapper class to the new utility functions and CLI tools.

## Why Migrate?

The `AITrader` class added unnecessary abstraction over Backtrader, hiding its flexibility and power. The new approach provides:

- **Direct Backtrader access** - Full control over your backtests
- **Utility functions** - Helper functions for common tasks without wrapper overhead
- **CLI tool** - Config-driven backtests for production workflows
- **Better maintainability** - Less code, clearer patterns
- **Flexibility** - Use what you need, ignore what you don't

## Quick Migration Examples

### Example 1: Simple Backtest

**Before (AITrader):**
```python
from ai_trader.trader import AITrader
from ai_trader.backtesting.strategies.classic.sma import SMAStrategy

trader = AITrader(cash=1000000, commission=0.001425)
trader.add_one_stock("data/AAPL.csv")
trader.add_strategy(SMAStrategy, fast_period=10, slow_period=30)
results = trader.run()
```

**After (Utilities):**
```python
from ai_trader.utils.backtest import run_backtest
from ai_trader.backtesting.strategies.classic.sma import SMAStrategy

results = run_backtest(
    strategy=SMAStrategy,
    data_source="data/AAPL.csv",
    cash=1000000,
    commission=0.001425,
    strategy_params={"fast_period": 10, "slow_period": 30},
)
```

**Benefits:** Simpler, one function call, explicit parameters.

---

### Example 2: Step-by-Step Control

**Before (AITrader):**
```python
from ai_trader.trader import AITrader
from ai_trader.backtesting.strategies.classic.bbands import BBandsStrategy

trader = AITrader(cash=500000)
trader.add_one_stock("data/AAPL.csv")
trader.add_strategy(BBandsStrategy, period=20)
trader.add_sizer("percent", percents=90)
trader.add_analyzers(["sharpe", "drawdown", "trades"])
results = trader.run()
```

**After (Utilities):**
```python
from ai_trader.utils.backtest import (
    create_cerebro,
    add_stock_data,
    add_sizer,
    add_analyzers,
    print_results,
)
from ai_trader.backtesting.strategies.classic.bbands import BBandsStrategy

# Step 1: Create cerebro
cerebro = create_cerebro(cash=500000)

# Step 2: Add data
add_stock_data(cerebro, source="data/AAPL.csv")

# Step 3: Add strategy
cerebro.addstrategy(BBandsStrategy, period=20)

# Step 4: Configure sizer and analyzers
add_sizer(cerebro, "percent", percents=90)
add_analyzers(cerebro, ["sharpe", "drawdown", "trades"])

# Step 5: Run
initial_value = cerebro.broker.getvalue()
results = cerebro.run()
final_value = cerebro.broker.getvalue()

# Step 6: Print results
print_results(results, initial_value, final_value)
```

**Benefits:** Clear steps, full control, explicit Backtrader calls.

---

### Example 3: Portfolio Backtest

**Before (AITrader):**
```python
from ai_trader.trader import AITrader
from ai_trader.backtesting.strategies.portfolio.roc_rotation import ROCRotationStrategy

trader = AITrader(
    cash=2000000,
    data_dir="./data/tw_stock/",
    start_date="2020-01-01",
)
trader.add_strategy(ROCRotationStrategy, k=5, rebalance_days=30)
results = trader.run()  # Auto-loads stocks from data_dir
```

**After (Utilities):**
```python
from ai_trader.utils.backtest import (
    create_cerebro,
    add_portfolio_data,
    add_sizer,
    add_analyzers,
    print_results,
)
from ai_trader.backtesting.strategies.portfolio.roc_rotation import ROCRotationStrategy

cerebro = create_cerebro(cash=2000000)

# Explicitly load portfolio data
add_portfolio_data(
    cerebro,
    data_dir="./data/tw_stock/",
    start_date="2020-01-01",
)

cerebro.addstrategy(ROCRotationStrategy, k=5, rebalance_days=30)
add_sizer(cerebro, "percent", percents=95)
add_analyzers(cerebro, ["sharpe", "drawdown", "returns", "sqn"])

initial_value = cerebro.broker.getvalue()
results = cerebro.run()
final_value = cerebro.broker.getvalue()

print_results(results, initial_value, final_value)
```

**Benefits:** Explicit data loading, no magic auto-loading.

---

### Example 4: Using the CLI

**No AITrader equivalent - New feature!**

**Create config file** (`config/backtest/my_strategy.yaml`):
```yaml
broker:
  cash: 1000000
  commission: 0.001425

data:
  file: "data/AAPL.csv"
  start_date: "2020-01-01"

strategy:
  class: "SMAStrategy"
  params:
    fast_period: 10
    slow_period: 30

sizer:
  type: "percent"
  params:
    percents: 95

analyzers:
  - sharpe
  - drawdown
  - returns
```

**Run from command line:**
```bash
ai-trader run config/backtest/my_strategy.yaml
```

**Benefits:** Config-driven, version-controlled, reproducible.

---

## Migration Checklist

### 1. Update Imports

**Remove:**
```python
from ai_trader.trader import AITrader
```

**Add:**
```python
from ai_trader.utils.backtest import run_backtest  # Quick backtests
# OR
from ai_trader.utils.backtest import (  # Step-by-step control
    create_cerebro,
    add_stock_data,
    add_sizer,
    add_analyzers,
    print_results,
)
```

### 2. Choose Your Approach

**Option A: Quick Backtest**
- Use `run_backtest()` function
- One-liner for simple backtests
- Good for exploration and quick tests

**Option B: Step-by-Step**
- Use individual utility functions
- More control over each step
- Good for custom workflows

**Option C: Pure Backtrader**
- Use Backtrader directly
- Maximum flexibility
- Good for advanced users

**Option D: CLI**
- Use `ai-trader` command
- Config-driven approach
- Good for production, reproducibility

### 3. Update Code

Replace AITrader method calls:

| AITrader Method | New Approach |
|----------------|--------------|
| `AITrader()` | `create_cerebro()` or `run_backtest()` |
| `add_one_stock()` | `add_stock_data()` |
| `add_stocks()` | `add_portfolio_data()` |
| `add_strategy()` | `cerebro.addstrategy()` |
| `add_sizer()` | `add_sizer()` |
| `add_analyzers()` | `add_analyzers()` or `add_default_analyzers()` |
| `add_broker()` | `create_cerebro(cash=..., commission=...)` |
| `run()` | `cerebro.run()` |
| `plot()` | `cerebro.plot()` |
| `analyze()` | `print_results()` |

### 4. Test Your Code

Run your migrated code and check for:
- Same results as before
- No deprecation warnings
- Clearer, more explicit code

## Common Patterns

### Load Data

```python
# Single stock from file
add_stock_data(cerebro, source="data/AAPL.csv")

# Single stock from DataFrame
add_stock_data(cerebro, source=df, name="AAPL")

# Example data
add_stock_data(cerebro, source=None)

# Portfolio from directory
add_portfolio_data(cerebro, data_dir="./data/tw_stock/")
```

### Add Strategy

```python
# Without parameters
cerebro.addstrategy(SMAStrategy)

# With parameters
cerebro.addstrategy(SMAStrategy, fast_period=10, slow_period=30)
```

### Configure Position Sizing

```python
# Percent of capital
add_sizer(cerebro, "percent", percents=95)

# Fixed stake
add_sizer(cerebro, "fixed", stake=100)
```

### Add Analyzers

```python
# Default set (sharpe, drawdown, returns)
add_default_analyzers(cerebro)

# Custom selection
add_analyzers(cerebro, ["sharpe", "drawdown", "trades", "sqn"])
```

## Resources

- **Examples**: See `scripts/examples/` for complete working examples
- **Config Files**: See `config/backtest/` for YAML config examples
- **CLI Help**: Run `ai-trader --help` for CLI documentation
- **Strategy Code**: Check updated strategies in `ai_trader/backtesting/strategies/`

## Timeline

- **v0.2.0** (Current): AITrader deprecated, new utilities available
- **v0.3.0** (Future): AITrader will be removed entirely

## Need Help?

If you have questions or issues during migration:

1. Check the examples in `scripts/examples/`
2. Read this guide thoroughly
3. Review the utility function documentation
4. Open an issue on GitHub with your specific case

## Advantages of New Approach

✅ **Simpler**: Less abstraction, clearer code
✅ **More flexible**: Direct Backtrader access when needed
✅ **Better maintainability**: Less wrapper code to maintain
✅ **Easier to debug**: Clearer stack traces
✅ **More Pythonic**: Explicit is better than implicit
✅ **Better tested**: Focused utility functions
✅ **Production-ready**: CLI for config-driven workflows

---

**Bottom Line**: The new approach gives you the power of Backtrader with helpful utilities when you need them, without forcing you through an unnecessary wrapper.
