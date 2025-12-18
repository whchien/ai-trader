"""MCP tools for managing strategies."""

from ai_trader.backtesting.strategies import classic, portfolio
from ai_trader.cli import _get_strategies_from_module
from ai_trader.core.logging import get_logger
from ai_trader.mcp.models import ListStrategiesRequest, StrategyInfo, StrategiesResult

logger = get_logger(__name__)


async def list_strategies_tool(request: ListStrategiesRequest) -> StrategiesResult:
    """
    List available trading strategies.

    Returns information about classic (single-stock) and portfolio (multi-stock)
    strategies with descriptions.
    """
    classic_list: list[StrategyInfo] = []
    portfolio_list: list[StrategyInfo] = []

    try:
        if request.strategy_type in ("classic", "all"):
            strategies = _get_strategies_from_module(classic)
            for name, cls in strategies:
                # Extract first line of docstring as description
                doc = cls.__doc__.split("\n")[0] if cls.__doc__ else "No description"
                classic_list.append(
                    StrategyInfo(
                        name=name,
                        description=doc.strip(),
                        type="classic",
                    )
                )

        if request.strategy_type in ("portfolio", "all"):
            strategies = _get_strategies_from_module(portfolio)
            for name, cls in strategies:
                # Extract first line of docstring as description
                doc = cls.__doc__.split("\n")[0] if cls.__doc__ else "No description"
                portfolio_list.append(
                    StrategyInfo(
                        name=name,
                        description=doc.strip(),
                        type="portfolio",
                    )
                )

        return StrategiesResult(
            classic_strategies=classic_list,
            portfolio_strategies=portfolio_list,
        )

    except Exception as e:
        error_msg = f"Failed to list strategies: {str(e)}"
        logger.exception("Error in list_strategies_tool")
        raise ValueError(error_msg) from e
