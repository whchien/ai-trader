"""MCP tools for running backtests."""

import asyncio
import time
from pathlib import Path
from typing import List, Optional

import backtrader as bt
import yaml
from fastmcp import Context

from ai_trader.cli import _load_strategy_class
from ai_trader.core.logging import get_logger
from ai_trader.mcp.models import (
    AnalyzerResults,
    BacktestResult,
    QuickBacktestRequest,
    RunBacktestRequest,
)
from ai_trader.utils.backtest import run_backtest

logger = get_logger(__name__)


async def run_backtest_tool(
    request: RunBacktestRequest,
    ctx: Context,
) -> BacktestResult:
    """
    Run a backtest from a YAML configuration file.

    Supports both single-stock and portfolio strategies with configuration overrides.
    """
    try:
        await ctx.info(f"Loading configuration from {request.config_file}")

        # Load config file
        config_path = Path(request.config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {request.config_file}")

        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Apply overrides
        if request.strategy:
            config["strategy"]["class"] = request.strategy
        if request.cash is not None:
            config["broker"]["cash"] = request.cash
        if request.commission is not None:
            config["broker"]["commission"] = request.commission

        # Load strategy class
        strategy_config = config["strategy"]
        strategy_class = _load_strategy_class(strategy_config["class"])
        await ctx.info(f"Strategy loaded: {strategy_class.__name__}")

        # Get common parameters
        data_config = config.get("data", {})
        if "file" not in data_config:
            raise ValueError("Only single-stock backtests (data.file) are supported via MCP")

        await ctx.info(f"Data file: {data_config['file']}")
        await ctx.info("Starting backtest execution...")

        # Run backtest in executor to avoid blocking
        start_time = time.time()
        results = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: run_backtest(
                strategy=strategy_class,
                data_source=data_config["file"],
                cash=config["broker"]["cash"],
                commission=config["broker"]["commission"],
                start_date=data_config.get("start_date"),
                end_date=data_config.get("end_date"),
                sizer_type=config.get("sizer", {}).get("type", "percent"),
                sizer_params=config.get("sizer", {}).get("params", {}),
                analyzers=config.get("analyzers", ["sharpe", "drawdown", "returns"]),
                strategy_params=strategy_config.get("params", {}),
                print_output=False,
                plot=False,
            ),
        )
        execution_time = time.time() - start_time

        # Extract and format results
        result = _extract_backtest_results(results, strategy_class.__name__, execution_time)
        await ctx.info(f"Backtest complete: {result.return_pct:.2f}% return")

        return result

    except Exception as e:
        error_msg = f"Backtest failed: {str(e)}"
        await ctx.error(error_msg)
        logger.exception("Error in run_backtest_tool")
        raise


async def quick_backtest_tool(
    request: QuickBacktestRequest,
    ctx: Context,
) -> BacktestResult:
    """
    Quick backtest without configuration file.

    Simplified interface for ad-hoc testing on single stocks.
    """
    try:
        await ctx.info(f"Strategy: {request.strategy_name}")
        await ctx.info(f"Data file: {request.data_file}")

        # Load strategy class
        strategy_class = _load_strategy_class(request.strategy_name)
        await ctx.info(f"Strategy loaded: {strategy_class.__name__}")

        await ctx.info("Starting backtest execution...")

        # Run backtest in executor
        start_time = time.time()
        results = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: run_backtest(
                strategy=strategy_class,
                data_source=request.data_file,
                cash=request.cash,
                commission=request.commission,
                start_date=request.start_date,
                end_date=request.end_date,
                sizer_type="percent",
                sizer_params={"percents": 95},
                analyzers=["sharpe", "drawdown", "returns", "trades"],
                print_output=False,
                plot=False,
            ),
        )
        execution_time = time.time() - start_time

        # Extract and format results
        result = _extract_backtest_results(results, strategy_class.__name__, execution_time)
        await ctx.info(f"Backtest complete: {result.return_pct:.2f}% return")

        return result

    except Exception as e:
        error_msg = f"Quick backtest failed: {str(e)}"
        await ctx.error(error_msg)
        logger.exception("Error in quick_backtest_tool")
        raise


def _extract_backtest_results(
    results: List[bt.Strategy],
    strategy_name: str,
    execution_time: float,
) -> BacktestResult:
    """
    Extract structured results from Backtrader results.

    Args:
        results: List of strategy instances from cerebro.run()
        strategy_name: Name of the strategy
        execution_time: Execution time in seconds

    Returns:
        BacktestResult with extracted metrics
    """
    if not results or len(results) == 0:
        raise ValueError("No results returned from backtest")

    strat = results[0]

    # Get broker values
    initial_value = strat.broker.startingcash
    final_value = strat.broker.getvalue()
    profit_loss = final_value - initial_value
    return_pct = (final_value / initial_value - 1) * 100 if initial_value != 0 else 0

    # Extract analyzer results
    analyzer_results = AnalyzerResults()

    # Sharpe Ratio
    if hasattr(strat.analyzers, "sharpe"):
        try:
            sharpe_data = strat.analyzers.sharpe.get_analysis()
            analyzer_results.sharpe_ratio = sharpe_data.get("sharperatio")
        except Exception as e:
            logger.warning(f"Could not extract Sharpe ratio: {e}")

    # Returns
    if hasattr(strat.analyzers, "returns"):
        try:
            returns_data = strat.analyzers.returns.get_analysis()
            analyzer_results.total_return = returns_data.get("rtot", 0) * 100
            analyzer_results.annualized_return = returns_data.get("rnorm", 0) * 100
        except Exception as e:
            logger.warning(f"Could not extract returns: {e}")

    # Drawdown
    if hasattr(strat.analyzers, "drawdown"):
        try:
            dd_data = strat.analyzers.drawdown.get_analysis()
            if "max" in dd_data and "drawdown" in dd_data["max"]:
                analyzer_results.max_drawdown = dd_data["max"]["drawdown"]
        except Exception as e:
            logger.warning(f"Could not extract drawdown: {e}")

    # Trade Analysis
    if hasattr(strat.analyzers, "trades"):
        try:
            trades_data = strat.analyzers.trades.get_analysis()
            total_trades = trades_data.get("total", {}).get("total", 0)
            analyzer_results.total_trades = total_trades

            if total_trades > 0:
                won = trades_data.get("won", {}).get("total", 0)
                lost = trades_data.get("lost", {}).get("total", 0)
                analyzer_results.won_trades = won
                analyzer_results.lost_trades = lost
                analyzer_results.win_rate = (won / total_trades) * 100
        except Exception as e:
            logger.warning(f"Could not extract trade analysis: {e}")

    return BacktestResult(
        strategy_name=strategy_name,
        initial_value=initial_value,
        final_value=final_value,
        profit_loss=profit_loss,
        return_pct=return_pct,
        analyzers=analyzer_results,
        execution_time_seconds=execution_time,
    )
