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
Root Coordinator Agent
├── Strategy Analysis Agent (market analysis & strategy recommendations)
├── Backtesting Execution Agent (runs backtests with different parameters)
├── Performance Evaluation Agent (analyzes results & generates insights)
├── Risk Assessment Agent (evaluates risk metrics & portfolio health)
└── Optimization Agent (parameter tuning & strategy enhancement)
```

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

### Basic Usage

```bash
# Start the agentic backtesting engine
adk run trading_backtester

# Or use the web interface
adk web
```

### Example Interactions

```
User: "I want to backtest momentum strategies on AAPL for the last year"

Agent: I'll help you backtest momentum strategies on AAPL. Let me:
1. Analyze AAPL's market conditions over the last year
2. Recommend suitable momentum strategies
3. Run backtests with optimized parameters
4. Provide comprehensive performance analysis

[Agent proceeds to coordinate the workflow automatically]
```

## Agent Details

### Root Coordinator Agent
- **Role**: Orchestrates the entire backtesting workflow
- **Capabilities**: Natural language understanding, task delegation, session management

### Strategy Analysis Agent  
- **Role**: Market analysis and strategy recommendation
- **Tools**: Market data fetchers, technical analysis, regime detection
- **Integration**: Uses ai_trader.data.fetchers and Google Search

### Backtesting Execution Agent
- **Role**: Executes backtests using existing ai_trader framework
- **Tools**: Wraps ai_trader.utils.backtest functions
- **Capabilities**: Single/portfolio backtests, parameter sweeps, parallel execution

### Performance Evaluation Agent
- **Role**: Deep analysis of backtest results
- **Tools**: Advanced metrics, statistical analysis, visualization
- **Capabilities**: Multi-strategy comparison, regime analysis, pattern detection

### Risk Assessment Agent
- **Role**: Comprehensive risk analysis
- **Tools**: VaR/CVaR, stress testing, Monte Carlo simulation
- **Capabilities**: Portfolio risk, correlation analysis, tail risk assessment

### Optimization Agent
- **Role**: Strategy and parameter optimization
- **Tools**: Grid search, Bayesian optimization, genetic algorithms
- **Capabilities**: Walk-forward analysis, ensemble creation, overfitting detection

## Integration with ai_trader

The agentic engine seamlessly integrates with the existing ai_trader framework:

- **Strategies**: Uses all 20+ existing strategies from ai_trader.backtesting.strategies
- **Data**: Leverages ai_trader.data.fetchers for market data
- **Execution**: Wraps ai_trader.utils.backtest functions
- **Configuration**: Generates and uses existing YAML config system

## Development Status

- [x] Architecture Design
- [x] Tool Specifications
- [ ] Root Coordinator Agent (In Progress)
- [ ] Strategy Analysis Agent
- [ ] Backtesting Execution Agent
- [ ] Performance Evaluation Agent
- [ ] Risk Assessment Agent
- [ ] Optimization Agent

## License

Licensed under the Apache License, Version 2.0.