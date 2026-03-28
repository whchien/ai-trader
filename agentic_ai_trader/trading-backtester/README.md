# Agentic Trading Strategy Backtesting Engine

An intelligent multi-agent system for automated trading strategy backtesting, analysis, and optimization built on Google ADK and the ai_trader framework.

## Overview

This agentic engine transforms traditional backtesting from a manual, iterative process into an intelligent, conversational workflow. Instead of manually configuring parameters and analyzing results, you can simply describe what you want to test in natural language.

### Key Features

- **Natural Language Interface**: "Backtest momentum strategies on tech stocks for the last 2 years"
- **Intelligent Strategy Selection**: AI recommends optimal strategies based on market conditions
- **Automated Parameter Optimization**: No more manual parameter tuning
- **Comprehensive Analysis**: Beyond basic metrics to actionable insights
- **Multi-Agent Architecture**: Specialized agents for different aspects of backtesting

### Agent Architecture

```
Root Coordinator Agent (orchestrates workflow)
├── Strategy Analysis Agent (analyzes market conditions & recommends strategies)
├── Backtesting Execution Agent (executes backtests & fetches market data)
├── Trader Agent (executes simulated/mock trades)
│   └── [MOCK TRADING ONLY - No real capital at risk]
│
├── Direct Utility Tools:
│   ├── get_available_strategies
│   ├── get_market_data_summary
│   ├── save_session_state
│   └── load_session_state
│
└── [Future Agents - Phase 2]:
    ├── Performance Evaluation Agent (deep analysis & insights)
    ├── Risk Assessment Agent (risk metrics & stress testing)
    └── Optimization Agent (parameter tuning & optimization)
```

**Current Implementation Status**: 3 of 5 planned agents are operational

## Quick Start

### Prerequisites

- Python 3.10+
- Google Cloud Project with Vertex AI enabled
- ai_trader framework (existing in parent directory)

### Installation

```bash
# Install dependencies
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env with your Google Cloud settings
```

### Running the System

```bash
# Start via web interface (recommended)
adk web

# Or run directly
adk run trading_backtester
```

Then type your backtesting requests in natural language!

## How It Works

### Typical Workflow

```
1. You provide a natural language request
   ↓
2. Root Coordinator understands the intent
   ↓
3. Coordinator routes to appropriate sub-agent(s):
   - Strategy Analysis Agent (for market analysis)
   - Backtesting Execution Agent (for running backtests)
   - Trader Agent (for executing simulated trades)
   ↓
4. Sub-agents access their specialized tools:
   - Fetch market data
   - Run backtests
   - Execute mock trades
   ↓
5. Results stored in session state for next step
   ↓
6. Coordinator synthesizes results and returns to you
```

### Agent Communication

- **Root Coordinator ↔ Sub-Agents**: Via AgentTool interface
- **Sub-Agents ↔ Tools**: Via ADK tools interface
- **State Sharing**: Via CallbackContext.state (dict passed between all agents)
- **Output Keys**: Each agent writes to specific session state key for next agent to read

### Example Flow: Backtest → Trade

```
User Input: "Backtest SMA on AAPL, then execute mock trades"
                           ↓
Root Coordinator routes to Backtesting Execution Agent
    - Fetches AAPL data (last 1 year)
    - Runs SMA backtest
    - Stores results in state["backtesting_execution_output"]
                           ↓
Root Coordinator routes to Trader Agent
    - Reads state["backtesting_execution_output"]
    - Extracts trade signals
    - Executes 5 MARKET orders for AAPL
    - Stores mock orders in state["mock_trade_orders"]
                           ↓
Results presented to user with:
    - Backtest metrics (Sharpe, return %, drawdown)
    - Mock order list with MOCK-XXXXXXXX IDs
    - Disclaimer: "THIS IS A SIMULATED ORDER"
```

### Example Interactions

#### Example 1: Complete Backtesting Workflow
```
User: "Backtest momentum strategies on AAPL for the last 2 years, then execute mock trades"

Root Coordinator:
1. Calls Strategy Analysis Agent to analyze AAPL market conditions
2. Calls Backtesting Execution Agent to run momentum strategy backtests
3. Calls Trader Agent to execute simulated trades based on results
4. Provides summary with backtest metrics and mock trade performance

Key Results Stored in Session:
- strategy_analysis_output: Market analysis & strategy recommendations
- backtesting_execution_output: Sharpe, return %, max drawdown, trades count
- trader_execution_output: Mock orders executed
- mock_trade_orders: List of MOCK-XXXXXXXX order IDs with details
```

#### Example 2: Quick Strategy Comparison
```
User: "Compare RSI and Bollinger Bands strategies on TSLA for 2024"

Root Coordinator:
1. Calls Backtesting Execution Agent with both strategies
2. Agent fetches TSLA data and runs both backtests in parallel
3. Provides side-by-side performance comparison

Results:
- Total return comparison
- Sharpe ratio, max drawdown metrics
- Win/loss ratio, average trades per month
```

#### Example 3: Market Analysis Only
```
User: "What trading strategies would work well for tech stocks in the current market?"

Root Coordinator:
- Calls Strategy Analysis Agent
- Provides market regime analysis and strategy recommendations
- No backtesting or trading executed
```

## Sub-Agent Architecture & Quality Standards

All sub-agents follow professional-grade prompt engineering standards:

### Prompt Structure (All Agents)
Each sub-agent prompt includes:
- **Role**: Clear expert persona definition (e.g., "Quantitative Trading Strategy Analyst")
- **Objective**: Specific goal and scope of the agent
- **Inputs Section**: Explicit list of state keys and parameters the agent reads
- **Mandatory Process**: Numbered workflow steps (not loose bullet points)
- **Output Schema**: Exact structure and fields the agent must produce
- **Error Handling**: Clear instructions for tool failures or missing inputs

### Agent Code Organization
- **Model Constants**: Each agent has `MODEL = config.get_model("root_agent")` at module level
- **Description Fields**: Each agent includes `description=` for orchestration awareness
- **Direct Instantiation**: Clean, direct agent creation (no factory function wrappers)
- **Module-Level Prompts**: Prompts are `PROMPT_NAME` module constants (not functions)

This structure ensures consistency, clarity, and professional-grade behavior across all agents.

## Agent Details

### Root Coordinator Agent
- **Role**: Orchestrates entire backtesting and trading workflows
- **Architecture**: LlmAgent with AgentTool sub-agent wrappers
- **Capabilities**:
  - Natural language request understanding
  - Sub-agent delegation via AgentTool interface
  - Session state management
  - Direct access to utility tools

### Strategy Analysis Agent ✅ (Implemented)
- **Role**: Quantitative Trading Strategy Analyst - identifies market regime and recommends optimal strategies
- **Tools**: None (pure reasoning agent)
- **Input**:
  - Symbol/Ticker to analyze
  - Market data (price, volatility, technical indicators)
  - Recent market observations from context
- **Output Structure**:
  - **Executive Summary**: Critical findings and overall outlook (2-3 bullets)
  - **Market Regime Assessment**: Identified regime (BULL/BEAR/SIDEWAYS/VOLATILE) with confidence level and supporting evidence
  - **Top 3 Strategy Recommendations**: For each strategy:
    - Rationale and why it fits current regime
    - Entry/exit logic and optimal parameters
    - Expected performance range
    - Applicable conditions
  - **Strategy Ranking Justification**: Why each strategy is ranked accordingly
  - **Risk & Regime Change Alerts**: Market moves that would invalidate analysis
- **Session Output Key**: `strategy_analysis_output`
- **Prompt Quality**: Professional-grade with detailed mandatory workflow and structured output schema

### Backtesting Execution Agent ✅ (Implemented)
- **Role**: Quantitative Backtesting Specialist - validates strategy recommendations through rigorous historical simulation
- **Tools**:
  - `fetch_market_data` - Gets OHLCV data for US/Taiwan stocks, crypto, forex
  - `quick_backtest` - Runs single-strategy backtests
  - `run_backtest_from_config` - Runs backtests from YAML config
  - `get_available_strategies` - Verifies strategy availability in framework
- **Input**:
  - Symbol/Ticker from `strategy_analysis_output`
  - Strategy recommendations from previous analysis
  - Timeframe, initial capital, commission rate
- **Output Structure**:
  - **Execution Summary**: Data period, quality, strategies tested
  - **Backtest Results Table**: Strategy | Total Return | CAGR | Sharpe | Max DD | Win Rate | Trades
  - **Per-Strategy Deep Dive**: Return %, CAGR, Sharpe ratio, max drawdown, win rate, profit factor, avg duration
  - **Best Performer Summary**: Ranking and recommendation strength
  - **Risk & Data Caveats**: Past performance disclaimer, data quality notes, commission impact
  - **Error Handling**: Failed backtests and fallback recommendations
- **Capabilities**:
  - Single/portfolio backtests
  - Strategy availability verification
  - Multiple market data sources
  - Comprehensive metrics (Sharpe, drawdown, returns, win rate, profit factor)
  - Comparative analysis across strategies
- **Session Output Key**: `backtesting_execution_output`
- **Prompt Quality**: Professional-grade with 6-step mandatory process and comprehensive output schema

### Trader Agent ✅ (Implemented - MOCK TRADING ONLY)
- **Role**: Simulated Trade Execution Specialist - converts validated strategies into executable trade plans (simulation only)
- **Tools**:
  - `mock_execute_trade` - Simulates trade order placement
    - Supports MARKET and LIMIT order types
    - Generates realistic order IDs (MOCK-XXXXXXXX format)
    - Simulates fill prices with realistic slippage
    - Tracks order status (FILLED/PENDING)
- **Input**:
  - Backtesting results from `backtesting_execution_output`
  - Available capital for simulated trading
  - Strategy entry signals and parameters
- **Output Structure**:
  - **⚠️ CRITICAL SIMULATION DISCLAIMER** (prominent at top/bottom): This is a MOCK trading environment, no real capital is at risk
  - **Trade Execution Summary**: Strategy applied, signal type, market price, capital deployed
  - **Trade Execution Plan**: Action (BUY/SELL), quantity, order type, fill price estimate, rationale
  - **Executed Order Details**: Order ID, symbol, action, quantity, fill price, timestamp, status
  - **Portfolio Status**: Capital deployed, remaining cash, open positions, estimated portfolio value
  - **Monitoring & Next Steps**: Key levels to watch, stop loss/take profit targets, signal to exit, review frequency
  - **Important Reminders**: Comparison to backtest expectations, simulation vs. real world differences
- **Features**:
  - ✅ All trades are SIMULATED - NO REAL CAPITAL AT RISK
  - ✅ Perfect for strategy testing, validation, and learning
  - ✅ Order tracking via mock_trade_orders list
  - ✅ Prominent MOCK TRADE DISCLAIMER in all outputs (multiple emphasis levels)
  - ✅ Realistic order mechanics (MARKET/LIMIT, slippage simulation, fill verification)
- **Order Output Format**:
  ```json
  {
    "order_id": "MOCK-A1B2C3D4",
    "status": "FILLED|PENDING",
    "symbol": "AAPL",
    "action": "BUY|SELL",
    "quantity": 100,
    "order_type": "MARKET|LIMIT",
    "limit_price": 150.00,
    "fill_price": 149.95,
    "timestamp": "2026-03-09T14:30:00Z",
    "warning": "THIS IS A SIMULATED ORDER. No real trade was placed. This is for testing and learning purposes only."
  }
  ```
- **Session Output Keys**:
  - `trader_execution_output` - Execution summary with trade plan and portfolio status
  - `mock_trade_orders` - List of all simulated orders with MOCK-XXXXXXXX IDs
- **Prompt Quality**: Professional-grade with 6-step execution process, prominent disclaimers, and structured output schema

### Direct Utility Tools (Root Coordinator)
- `get_available_strategies` - Lists all 20+ trading strategies from ai_trader
- `get_market_data_summary` - Quick overview for any symbol
- `save_session_state` - Persists workflow state
- `load_session_state` - Restores previous workflow

### Future Agents (Phase 2 - Not Yet Implemented)

#### Performance Evaluation Agent
- **Planned Role**: Deep analysis of backtest results
- **Planned Tools**: Advanced metrics, statistical analysis, visualization
- **Planned Capabilities**: Multi-strategy comparison, regime analysis, pattern detection

#### Risk Assessment Agent
- **Planned Role**: Comprehensive risk analysis
- **Planned Tools**: VaR/CVaR, stress testing, Monte Carlo simulation
- **Planned Capabilities**: Portfolio risk, correlation analysis, tail risk assessment

#### Optimization Agent
- **Planned Role**: Strategy and parameter optimization
- **Planned Tools**: Grid search, Bayesian optimization, genetic algorithms
- **Planned Capabilities**: Walk-forward analysis, ensemble creation, overfitting detection

## Integration with ai_trader

The agentic engine seamlessly integrates with the existing ai_trader framework:

### Data Integration
- **Market Data Fetchers**: USStockFetcher, TWStockFetcher, CryptoDataFetcher, ForexDataFetcher, VIXDataFetcher
- **Supported Markets**: US stocks, Taiwan stocks, cryptocurrencies, forex, VIX index
- **Data Storage**:
  - **CSV (Default)**: Backward-compatible, transparent file storage
  - **SQLite (New)**: Persistent caching with incremental updates
  - **Both**: Save to both CSV and SQLite simultaneously

### Persistent Data Storage with SQLite

The ai-trader framework now includes a powerful SQLite storage layer using SQLModel ORM for persistent, efficient data caching. This eliminates redundant API calls and speeds up repeated backtests.

#### Quick Start: Using SQLite Storage

```bash
# First fetch: Stores in SQLite + returns data
ai-trader fetch AAPL --market us_stock --start-date 2024-01-01 --storage sqlite

# Second fetch: Loads from cache instantly (no API call)
ai-trader fetch AAPL --market us_stock --start-date 2024-01-01 --storage sqlite

# Fetch with both CSV and SQLite
ai-trader fetch AAPL --market us_stock --start-date 2024-01-01 --storage both

# Default: CSV only (existing behavior)
ai-trader fetch AAPL --market us_stock --start-date 2024-01-01
```

#### Architecture: SQLModel with Multi-Market Tables

The storage layer uses **SQLModel ORM** (no raw SQL strings) with separate tables per market:

```
database: data/market_data.db

Tables:
├── us_stock_data      (US stocks with adj_close)
├── tw_stock_data      (Taiwan stocks, no adj_close)
├── crypto_data        (Cryptocurrencies with adj_close)
├── forex_data         (Forex pairs, volume=0, has adj_close)
├── vix_data           (VIX index)
└── data_metadata      (Coverage tracking for each ticker)
```

**Why separate tables?**
- Different markets have different optional columns (adj_close not in TW stocks)
- Cleaner schema without unnecessary nullable fields
- Optimal query performance (no cross-market JOINs)
- Market-specific metadata tracking

#### Smart Incremental Updates

The system automatically detects what data is already cached:

```python
from ai_trader.data.storage import SQLiteDataStorage

storage = SQLiteDataStorage(db_path="data/market_data.db")

# Check what date range is already cached
coverage = storage.get_coverage("AAPL", "us_stock")
# Returns: (date(2024,1,1), date(2024,1,15))

# Calculate missing ranges for desired period
missing = storage.get_missing_ranges("AAPL", "us_stock",
                                     "2024-01-01", "2024-02-01")
# Returns: [(date(2024,1,16), date(2024,2,01))]
# Only fetches 2024-01-16 to 2024-02-01 from API
```

#### Data Management Commands

```bash
# List all cached tickers
ai-trader data list

# Filter by market
ai-trader data list --market us_stock

# Get database info
ai-trader data info
# Output:
#   Path: /path/to/data/market_data.db
#   Size: 2.5 MB
#   Total tickers: 45
#   Tickers by market:
#     • us_stock   : 20 tickers
#     • tw_stock   : 15 tickers
#     • crypto     : 10 tickers

# Delete specific ticker
ai-trader data delete --ticker AAPL --market us_stock

# Clean old data (before 2020)
ai-trader data clean --market us_stock --before 2020-01-01
```

#### Using SQLite in Code

```python
import pandas as pd
from ai_trader.data.storage import SQLiteDataStorage

# Initialize storage
storage = SQLiteDataStorage(db_path="data/market_data.db")

# Save data to database
df = pd.DataFrame(...)  # OHLCV data with DatetimeIndex
rows_saved = storage.save(df=df, ticker="AAPL", market_type="us_stock")

# Load data from database
df = storage.load("AAPL", "us_stock", "2024-01-01", "2024-01-31")

# List all cached tickers
tickers = storage.list_tickers()  # or filter by market_type

# Get database statistics
info = storage.get_database_info()
print(f"Database size: {info['size_bytes']:,} bytes")
print(f"Total tickers: {info['total_tickers']}")
```

#### Data Models (SQLModel)

Each table is defined using SQLModel for type safety and ORM operations:

```python
from ai_trader.data.storage import USStockData, TWStockData, CryptoData

# Models define schema with proper constraints:
# - UNIQUE(ticker, date) - No duplicate entries for same symbol on same date
# - Indexed: ticker, date - Fast lookups
# - Optional fields: adj_close (only in stocks, crypto)

# All models inherit common OHLCV fields:
# - ticker: str
# - date: date
# - open, high, low, close: float
# - volume: float
# - adj_close: Optional[float]  (some markets only)
```

#### Best Practices

1. **Default to SQLite for repeated backtests**: Avoid redundant API calls
   ```bash
   # Good: Reuse cached data
   ai-trader fetch AAPL --start-date 2024-01-01 --storage sqlite
   ai-trader quick SMAStrategy data/AAPL.csv  # Uses same cached data
   ```

2. **Use CSV for sharing**: Share files with team members
   ```bash
   ai-trader fetch AAPL --start-date 2024-01-01 --storage csv
   # Commit data/us_stock/AAPL_2024-01-01_to_2024-12-31.csv to git
   ```

3. **Combined: Best of both worlds**
   ```bash
   ai-trader fetch AAPL --start-date 2024-01-01 --storage both
   # Persists in SQLite + exports CSV for sharing
   ```

4. **Periodic cleanup**: Remove data older than backtest horizon
   ```bash
   ai-trader data clean --market us_stock --before 2020-01-01
   ```

#### Performance Comparison

| Operation | CSV | SQLite |
|-----------|-----|--------|
| First fetch (500 rows) | ~2s (API call) | ~2s (API call) |
| Repeated fetch (same data) | ~2s (API call) | ~50ms (from DB) |
| Incremental fetch (new data) | ~2s (API call) | ~500ms (partial API + DB) |
| Query 1 year of data | ~100ms (file I/O) | ~30ms (indexed query) |
| Database size | - | ~50KB per 1000 rows |

### Strategy Integration
- **Available Strategies**: 20+ strategies from ai_trader.backtesting.strategies
  - Trend-following: SMA, Turtle, RSRS
  - Momentum: RSI, MACD, Momentum, ROC, VCP
  - Mean-reversion: Bollinger Bands
  - Portfolio-based: Rotation strategies
- **Dynamic Loading**: Strategies loaded by class name at runtime
- **Parameter Support**: Custom parameters passed to strategies

### Backtesting Integration
- **Execution**: Wraps ai_trader.utils.backtest functions
- **Analysis**: Uses ai_trader analytics for Sharpe, drawdown, returns
- **Configuration**: Supports YAML config files or direct parameters
- **Commission**: Default 0.1425% (customizable)
- **Position Sizing**: 95% of capital by default

### Session State and Persistence
- **Storage**: Uses ADK CallbackContext.state for multi-agent coordination
- **Keys**:
  - `strategy_analysis_output` - Strategy recommendations
  - `backtesting_execution_output` - Backtest results
  - `trader_execution_output` - Trade execution summary
  - `mock_trade_orders` - List of simulated orders
  - `fetched_data_files` - Paths to downloaded data
- **Save/Load**: Manual session state persistence via tools

## Example Prompts for Testing

### Prompt 1: Complete Workflow with Trading
```
"Backtest momentum strategies on AAPL for 2024, then execute mock trades based on the best performing strategy"
```
**What happens:**
1. Strategy Analysis Agent analyzes AAPL's 2024 conditions
2. Backtesting Execution Agent fetches AAPL data and runs momentum strategies
3. Trader Agent executes simulated trades with MARKET orders
4. Results show backtest metrics + mock trade orders in session state

**Session State after completion:**
- `strategy_analysis_output`: Market analysis & recommendations
- `backtesting_execution_output`: Sharpe ratio, return %, max drawdown, trades
- `trader_execution_output`: Summary of mock trades
- `mock_trade_orders`: List of MOCK-XXXXXXXX orders with fills

### Prompt 2: Strategy Comparison
```
"Compare SMA, RSI, and MACD strategies on Bitcoin for the last year. Which one has the best Sharpe ratio?"
```
**What happens:**
1. Backtesting Execution Agent fetches Bitcoin data
2. Runs all three strategies in parallel
3. Provides side-by-side comparison with metrics

### Prompt 3: Market Analysis Only
```
"What strategies would be best for a sideways tech stock market right now?"
```
**What happens:**
1. Strategy Analysis Agent provides pure market analysis
2. No backtesting or trading executed
3. Recommendations based on market regime and strategy characteristics

### Prompt 4: Quick Single Strategy Test
```
"Backtest the RSI strategy on Tesla for 2024"
```
**What happens:**
1. Backtesting Execution Agent fetches Tesla data
2. Runs RSI backtest with default parameters
3. Returns metrics and trade list

### Prompt 5: Save and Load Workflow
```
First: "Backtest momentum strategies on AAPL. Save the results."
Later: "Load the AAPL momentum backtest results and execute mock trades"
```
**What happens:**
1. First request: Results saved in session state
2. Second request: Previous state loaded, trades executed
3. Demonstrates session persistence across multiple requests

## Development Status

### Phase 1: Core Multi-Agent System ✅ COMPLETE
- [x] Root Coordinator Agent (with AgentTool sub-agent wrappers)
- [x] Strategy Analysis Agent (pure reasoning)
- [x] Backtesting Execution Agent (with MCP tools)
- [x] Trader Agent (mock/simulated trading only)
- [x] Session state persistence
- [x] Documentation and examples

### Phase 2: Advanced Analytics (Future)
- [ ] Performance Evaluation Agent (deep analysis & insights)
- [ ] Risk Assessment Agent (VaR, stress testing, Monte Carlo)
- [ ] Optimization Agent (parameter tuning & walk-forward analysis)

### Phase 3: Production Features (Future)
- [ ] Real trade execution (with proper risk controls)
- [ ] Portfolio backtesting (multi-asset strategies)
- [ ] Advanced visualizations and reporting
- [ ] Integration with live market data feeds

## License

Licensed under the Apache License, Version 2.0.