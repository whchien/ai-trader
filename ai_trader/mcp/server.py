"""Main MCP server for ai-trader."""

from fastmcp import Context, FastMCP

from ai_trader.mcp import models
from ai_trader.mcp.tools import backtest, data, strategies

# Initialize MCP server
mcp = FastMCP("ai-trader")


@mcp.tool
async def run_backtest(request: models.RunBacktestRequest, ctx: Context) -> models.BacktestResult:
    """
    Run a backtest from a YAML configuration file.

    Supports single-stock strategies with full configuration options including
    strategy parameters, broker settings, and analyzers.

    Args:
        request: Configuration for the backtest run

    Returns:
        Detailed backtest results with metrics
    """
    return await backtest.run_backtest_tool(request, ctx)


@mcp.tool
async def quick_backtest(
    request: models.QuickBacktestRequest, ctx: Context
) -> models.BacktestResult:
    """
    Quick backtest without a configuration file.

    Ideal for ad-hoc testing with minimal setup. Only supports single-stock strategies
    with default position sizing (95%).

    Args:
        request: Strategy name, data file, and parameters

    Returns:
        Detailed backtest results with metrics
    """
    return await backtest.quick_backtest_tool(request, ctx)


@mcp.tool
async def fetch_market_data(request: models.FetchDataRequest, ctx: Context) -> models.FetchResult:
    """
    Fetch market data and save to CSV files.

    Supports US stocks, Taiwan stocks, cryptocurrencies, forex, and VIX index.
    Can fetch multiple symbols in batch mode for improved performance.

    Args:
        request: Symbols, market type, and date range

    Returns:
        Status of fetch operation with file paths
    """
    return await data.fetch_data_tool(request, ctx)


@mcp.tool
async def list_strategies(request: models.ListStrategiesRequest) -> models.StrategiesResult:
    """
    List available trading strategies.

    Returns all classic (single-stock) and portfolio (multi-stock) strategies
    with descriptions and metadata.

    Args:
        request: Filter for strategy type

    Returns:
        List of available strategies organized by type
    """
    return await strategies.list_strategies_tool(request)


__all__ = ["mcp"]
