# Example Scripts

This directory contains example scripts demonstrating different ways to use ai-trader for backtesting.

## Running Examples

Make the scripts executable:

```bash
chmod +x scripts/examples/*.py
```

Run an example:

```bash
python scripts/examples/01_simple_backtest.py
```

Or directly if executable:

```bash
./scripts/examples/01_simple_backtest.py
```

## Examples Overview

### 01_simple_backtest.py

**Purpose:** Quickstart example using the `run_backtest()` convenience function.

**What it demonstrates:**
- Running a complete backtest with one function call
- Using the SMA (Simple Moving Average) strategy
- Passing strategy parameters
- Using example data

**Recommended for:** Beginners who want to get started quickly.

### 02_step_by_step.py

**Purpose:** Shows each step of the backtest process explicitly.

**What it demonstrates:**
- Creating a Cerebro instance
- Loading stock data
- Adding a strategy
- Configuring position sizer
- Adding analyzers
- Running backtest and printing results

**Recommended for:** Users who want full control over each step.

### 03_portfolio_backtest.py

**Purpose:** Demonstrates portfolio/multi-stock backtesting.

**What it demonstrates:**
- Loading multiple stocks from a directory
- Using a rotation strategy
- Position sizing across multiple positions
- Portfolio-specific analyzers (SQN)

**Recommended for:** Users building portfolio strategies.

### 04_pure_backtrader.py

**Purpose:** Shows pure Backtrader usage without any helper functions.

**What it demonstrates:**
- Direct Backtrader API usage
- Creating custom strategies inline
- Full flexibility and control
- Manual result extraction

**Recommended for:** Advanced users who want maximum flexibility or are already familiar with Backtrader.

### 05_compare_strategies.py

**Purpose:** Compare multiple strategies on the same data.

**What it demonstrates:**
- Running multiple strategies programmatically
- Extracting and comparing metrics
- Finding the best-performing strategy
- Creating comparison tables

**Recommended for:** Strategy research and optimization.

## Common Patterns

### Loading Data

#### Use example data:
```python
add_stock_data(cerebro, source=None)
```

#### Load from CSV file:
```python
add_stock_data(cerebro, source="data/AAPL.csv")
```

#### Load from DataFrame:
```python
import pandas as pd
df = pd.read_csv("data/AAPL.csv", parse_dates=["Date"], index_col=["Date"])
add_stock_data(cerebro, source=df, name="AAPL")
```

#### Load portfolio:
```python
add_portfolio_data(cerebro, data_dir="./data/tw_stock/")
```

### Adding Strategies

#### With default parameters:
```python
cerebro.addstrategy(SMAStrategy)
```

#### With custom parameters:
```python
cerebro.addstrategy(SMAStrategy, fast_period=10, slow_period=30)
```

#### Using run_backtest:
```python
run_backtest(
    strategy=SMAStrategy,
    strategy_params={"fast_period": 10, "slow_period": 30}
)
```

### Position Sizing

#### Percent of capital:
```python
add_sizer(cerebro, "percent", percents=95)
```

#### Fixed stake:
```python
add_sizer(cerebro, "fixed", stake=100)
```

### Analyzers

#### Default set:
```python
add_default_analyzers(cerebro)  # sharpe, drawdown, returns
```

#### Custom selection:
```python
add_analyzers(cerebro, ["sharpe", "drawdown", "returns", "trades", "sqn"])
```

## Next Steps

1. **Modify an example:** Copy an example and modify it for your needs
2. **Create a custom strategy:** See `04_pure_backtrader.py` for inline strategy definition
3. **Use config files:** Try the CLI with config files in `config/backtest/`
4. **Explore strategies:** Check available strategies in `ai_trader/backtesting/strategies/`

## Tips

- Start with `01_simple_backtest.py` if you're new to backtesting
- Use `02_step_by_step.py` as a template for custom backtests
- Always compare your strategy against `BuyHoldStrategy` benchmark
- Include at least sharpe, drawdown, and returns analyzers
- Test on multiple time periods to validate robustness
- Consider transaction costs (commission parameter)

## Data Requirements

Most examples use `load_example()` which provides sample data. For real backtesting:

1. Download data using the CLI:
   ```bash
   ai-trader fetch AAPL --market us --start-date 2020-01-01
   ```

2. Or use your own CSV files with columns: `Date, Open, High, Low, Close, Volume`

## Questions?

- Check the main README.md for general documentation
- See config/backtest/README.md for YAML configuration docs
- Read strategy source code in ai_trader/backtesting/strategies/
