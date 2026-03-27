"""Trader Sub-Agent for simulated trade execution and portfolio management."""

from google.adk.agents import LlmAgent

from ...core.config import config
from .mock_trade_executor import mock_execute_trade
from .prompt import TRADER_PROMPT

MODEL = config.get_model("root_agent")

trader_agent = LlmAgent(
    name="trader_agent",
    model=MODEL,
    description="Executes simulated trades based on validated strategy signals and manages mock portfolio",
    instruction=TRADER_PROMPT,
    output_key="trader_execution_output",
    tools=[mock_execute_trade],
)
