"""Strategy Analysis Sub-Agent for market regime identification and strategy selection."""

from google.adk.agents import LlmAgent

from ...core.config import config
from .prompt import STRATEGY_ANALYSIS_PROMPT

MODEL = config.get_model("root_agent")

strategy_analysis_agent = LlmAgent(
    name="strategy_analysis_agent",
    model=MODEL,
    description="Analyzes market conditions, identifies market regime, and recommends optimal trading strategies",
    instruction=STRATEGY_ANALYSIS_PROMPT,
    output_key="strategy_analysis_output",
    tools=[],  # Pure reasoning, no tools required
)
