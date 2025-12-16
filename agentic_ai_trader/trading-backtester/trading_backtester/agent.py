"""Root Coordinator Agent for the trading backtester."""

import logging
from datetime import date

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.genai import types

from .core.config import config
from .prompts import get_root_coordinator_prompt
from .tools import (
    call_backtesting_execution_agent,
    call_optimization_agent,
    call_performance_evaluation_agent,
    call_risk_assessment_agent,
    call_strategy_analysis_agent,
    get_available_strategies,
    get_market_data_summary,
    load_session_state,
    save_session_state,
)

# Set up logging
logging.basicConfig(level=getattr(logging, config.get("logging.level", "INFO")))
logger = logging.getLogger(__name__)


def load_config_in_context(callback_context: CallbackContext):
    """Load configuration into the callback context on first use."""
    if "config" not in callback_context.state:
        callback_context.state["config"] = {
            "default_cash": config.get("backtesting.default_cash"),
            "default_commission": config.get("backtesting.default_commission"),
            "max_parallel_backtests": config.get("backtesting.max_parallel_backtests"),
            "data_dir": config.get("data.default_dir"),
        }
        logger.info("Configuration loaded into context")


def get_root_coordinator_agent() -> LlmAgent:
    """Create and configure the Root Coordinator Agent."""

    # Validate configuration
    config.validate()

    # Define tools for the root agent
    tools = [
        # Direct utility tools
        get_available_strategies,
        get_market_data_summary,
        save_session_state,
        load_session_state,
        # Agent delegation tools
        call_strategy_analysis_agent,
        call_backtesting_execution_agent,
        call_performance_evaluation_agent,
        call_risk_assessment_agent,
        call_optimization_agent,
    ]

    # Create the agent
    agent = LlmAgent(
        model=config.get_model("root_agent"),
        name="trading_backtester_coordinator",
        instruction=get_root_coordinator_prompt(),
        global_instruction=f"""
        You are the Root Coordinator for an intelligent trading strategy backtesting system.
        Today's date: {date.today()}
        
        Integration Details:
        - ai_trader framework with 20+ trading strategies available
        - Supports US stocks, Taiwan stocks, and cryptocurrencies
        - Built on Backtrader framework with comprehensive analytics
        - Default cash: ${config.get("backtesting.default_cash"):,}
        - Default commission: {config.get("backtesting.default_commission"):.4f}
        
        Your goal is to provide intelligent, comprehensive backtesting analysis through coordinated multi-agent workflows.
        """,
        tools=tools,
        before_agent_callback=load_config_in_context,
        generate_content_config=types.GenerateContentConfig(
            temperature=0.1,  # Low temperature for consistent, focused responses
            top_p=0.9,
            top_k=40,
        ),
    )

    logger.info(f"Root Coordinator Agent created with model: {config.get_model('root_agent')}")
    return agent


# Create the root agent instance
root_agent = get_root_coordinator_agent()


# Export for ADK
__all__ = ["root_agent"]
