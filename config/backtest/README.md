# Backtest Configuration Files

This directory contains example YAML configuration files for running backtests.

## Usage

Run a backtest using the CLI:

```bash
ai-trader run config/backtest/sma_example.yaml
```

Override parameters from command line:

```bash
ai-trader run config/backtest/bbands_example.yaml --cash 100000 --commission 0.002
```

## Configuration Structure

Each YAML file has the following structure:

### Broker Settings

```yaml
broker:
  cash: 1000000          # Initial capital
  commission: 0.001425   # Commission rate per trade
```

### Data Settings

For single stock:

```yaml
data:
  file: "data/AAPL.csv"     # Path to CSV file
  start_date: "2020-01-01"  # Optional: filter start date
  end_date: "2023-12-31"    # Optional: filter end date
  date_col: "date"          # Date column name ("date" or "Date")
```

For portfolio (multiple stocks):

```yaml
data:
  directory: "./data/tw_stock/"  # Directory with CSV files
  start_date: "2020-01-01"
  end_date: "2023-12-31"
  date_col: "date"
```

### Strategy Settings

```yaml
strategy:
  class: "SMAStrategy"    # Strategy class name
  params:                 # Strategy-specific parameters
    fast_period: 10
    slow_period: 30
```

### Position Sizer

```yaml
sizer:
  type: "percent"         # "percent" or "fixed"
  params:
    percents: 95          # For percent sizer
    # stake: 100          # For fixed sizer
```

### Analyzers

```yaml
analyzers:
  - sharpe      # Sharpe ratio
  - drawdown    # Maximum drawdown
  - returns     # Return metrics
  - trades      # Trade statistics
  - sqn         # System Quality Number
```

## Available Example Configs

- **sma_example.yaml** - Simple Moving Average crossover strategy
- **bbands_example.yaml** - Bollinger Bands mean reversion strategy
- **portfolio_example.yaml** - Multi-stock rotation strategy
- **crypto_example.yaml** - RSI strategy for cryptocurrency

## Creating Your Own Config

1. Copy an example config that matches your use case
2. Modify the data source (file or directory)
3. Choose your strategy and set parameters
4. Adjust broker settings (cash, commission)
5. Select desired analyzers
6. Run with: `ai-trader run your_config.yaml`

## Strategy Class Names

### Classic Strategies (Single Stock)

- `SMAStrategy` - Simple Moving Average crossover
- `EMAStrategy` - Exponential Moving Average crossover
- `BBandsStrategy` - Bollinger Bands
- `RSIStrategy` - Relative Strength Index
- `MACDStrategy` - Moving Average Convergence Divergence
- `KDJStrategy` - KDJ oscillator
- `StochasticStrategy` - Stochastic oscillator
- `WilliamsRStrategy` - Williams %R
- `CCIStrategy` - Commodity Channel Index
- `ATRStrategy` - Average True Range
- `DMIStrategy` - Directional Movement Index
- `OBVStrategy` - On-Balance Volume
- `BuyHoldStrategy` - Buy and hold benchmark

### Portfolio Strategies (Multi-Stock)

- `ROCRotationStrategy` - Rate of Change rotation
- `VolumeRotationStrategy` - Volume-based rotation
- `MomentumRotationStrategy` - Momentum rotation
- `LowVolatilityStrategy` - Low volatility selection

## Tips

- Start with small cash amounts for testing
- Use appropriate commission rates for your market:
  - Taiwan stocks: 0.001425
  - US stocks: 0.001
  - Crypto: 0.001-0.0025
- Always include at least 'sharpe', 'drawdown', 'returns' analyzers
- Test date ranges that include both bull and bear markets
- Compare results against BuyHoldStrategy benchmark
