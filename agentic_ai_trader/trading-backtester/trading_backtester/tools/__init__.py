"""Tools for the trading backtester agents."""

from .agent_tools import (
    call_backtesting_execution_agent,
    call_optimization_agent,
    call_performance_evaluation_agent,
    call_risk_assessment_agent,
    call_strategy_analysis_agent,
)
from .coordinator_tools import (
    get_available_strategies,
    get_market_data_summary,
    load_session_state,
    save_session_state,
)
from .mcp_tools import fetch_market_data, quick_backtest, run_backtest_from_config

__all__ = [
    # Coordinator tools
    "get_available_strategies",
    "get_market_data_summary",
    "save_session_state",
    "load_session_state",
    # MCP-wrapped tools
    "run_backtest_from_config",
    "quick_backtest",
    "fetch_market_data",
    # Agent delegation tools
    "call_strategy_analysis_agent",
    "call_backtesting_execution_agent",
    "call_performance_evaluation_agent",
    "call_risk_assessment_agent",
    "call_optimization_agent",
]
