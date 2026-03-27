"""Backtesting Execution Sub-Agent for strategy validation and performance analysis."""

from google.adk.agents import LlmAgent

from ...core.config import config
from ...tools.mcp_tools import (
    fetch_market_data,
    quick_backtest,
    run_backtest_from_config,
)
from ...tools.coordinator_tools import get_available_strategies
from .prompt import BACKTESTING_EXECUTION_PROMPT

MODEL = config.get_model("root_agent")

backtesting_execution_agent = LlmAgent(
    name="backtesting_execution_agent",
    model=MODEL,
    description="Executes backtests on recommended strategies and provides comprehensive performance metrics",
    instruction=BACKTESTING_EXECUTION_PROMPT,
    output_key="backtesting_execution_output",
    tools=[
        fetch_market_data,
        quick_backtest,
        run_backtest_from_config,
        get_available_strategies,
    ],
)
