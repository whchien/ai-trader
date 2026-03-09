"""ADK tools wrapping MCP backtest and data fetching functionality."""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import List, Optional

import yaml
from google.adk.tools import ToolContext

from ai_trader.cli import _load_strategy_class
from ai_trader.data.fetchers import (
    CryptoDataFetcher,
    ForexDataFetcher,
    TWStockFetcher,
    USStockFetcher,
    VIXDataFetcher,
)
from ai_trader.data.storage import FileManager
from ai_trader.mcp.tools.backtest import _extract_backtest_results
from ai_trader.utils.backtest import run_backtest

logger = logging.getLogger(__name__)


async def run_backtest_from_config(
    config_file: str,
    strategy: Optional[str] = None,
    cash: Optional[float] = None,
    commission: Optional[float] = None,
    tool_context: ToolContext = None,
) -> str:
    """Run a backtest from a YAML configuration file.

    Supports configuration overrides for strategy, cash, and commission.

    Args:
        config_file: Path to YAML configuration file
        strategy: Optional override for strategy class name
        cash: Optional override for initial cash amount
        commission: Optional override for commission rate
        tool_context: Tool context for state management

    Returns:
        JSON string with backtest results
    """
    logger.info(f"Running backtest from config: {config_file}")

    try:
        # Load config file
        config_path = Path(config_file)
        if not config_path.exists():
            return json.dumps({"error": f"Config file not found: {config_file}"})

        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Apply overrides
        if strategy:
            config["strategy"]["class"] = strategy
        if cash is not None:
            config["broker"]["cash"] = cash
        if commission is not None:
            config["broker"]["commission"] = commission

        # Load strategy class
        strategy_config = config["strategy"]
        strategy_class = _load_strategy_class(strategy_config["class"])
        logger.info(f"Strategy loaded: {strategy_class.__name__}")

        # Get common parameters
        data_config = config.get("data", {})
        if "file" not in data_config:
            return json.dumps({"error": "Only single-stock backtests (data.file) are supported"})

        logger.info(f"Data file: {data_config['file']}")
        logger.info("Starting backtest execution...")

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
        logger.info(f"Backtest complete: {result.return_pct:.2f}% return")

        # Store result in context if provided
        if tool_context:
            tool_context.state["last_backtest_result"] = result.model_dump()

        return json.dumps(result.model_dump(), indent=2)

    except Exception as e:
        error_msg = f"Backtest failed: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})


async def quick_backtest(
    strategy_name: str,
    data_file: str,
    cash: float = 1000000,
    commission: float = 0.001425,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    tool_context: ToolContext = None,
) -> str:
    """Run a quick backtest without configuration file.

    Simplified interface for ad-hoc testing on single stocks.

    Args:
        strategy_name: Strategy class name (e.g., 'SMAStrategy')
        data_file: Path to CSV data file
        cash: Initial cash amount (default: 1,000,000)
        commission: Commission rate (default: 0.001425)
        start_date: Optional start date in YYYY-MM-DD format
        end_date: Optional end date in YYYY-MM-DD format
        tool_context: Tool context for state management

    Returns:
        JSON string with backtest results
    """
    logger.info(f"Running quick backtest: {strategy_name} on {data_file}")

    try:
        # Load strategy class
        strategy_class = _load_strategy_class(strategy_name)
        logger.info(f"Strategy loaded: {strategy_class.__name__}")

        logger.info("Starting backtest execution...")

        # Run backtest in executor
        start_time = time.time()
        results = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: run_backtest(
                strategy=strategy_class,
                data_source=data_file,
                cash=cash,
                commission=commission,
                start_date=start_date,
                end_date=end_date,
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
        logger.info(f"Backtest complete: {result.return_pct:.2f}% return")

        # Store result in context if provided
        if tool_context:
            tool_context.state["last_backtest_result"] = result.model_dump()

        return json.dumps(result.model_dump(), indent=2)

    except Exception as e:
        error_msg = f"Quick backtest failed: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})


async def fetch_market_data(
    symbols: List[str],
    market: str = "us_stock",
    start_date: str = None,
    end_date: Optional[str] = None,
    output_dir: str = "./data",
    tool_context: ToolContext = None,
) -> str:
    """Fetch market data and save to CSV files.

    Supports US stocks, Taiwan stocks, cryptocurrencies, forex, and VIX index.
    Can fetch multiple symbols in batch mode.

    Args:
        symbols: List of symbols to fetch (e.g., ['AAPL', 'MSFT'])
        market: Market type ('us_stock', 'tw_stock', 'crypto', 'forex', 'vix')
        start_date: Start date in YYYY-MM-DD format (required)
        end_date: End date in YYYY-MM-DD format (optional, defaults to today)
        output_dir: Output directory for saved CSV files (default: './data')
        tool_context: Tool context for state management

    Returns:
        JSON string with fetch results
    """
    logger.info(f"Fetching {len(symbols)} symbol(s) from {market} market")

    if not start_date:
        return json.dumps({"error": "start_date is required"})

    try:
        # Factory mapping for fetcher classes
        fetcher_factory = {
            "us_stock": (USStockFetcher, "symbol"),
            "tw_stock": (TWStockFetcher, "symbol"),
            "crypto": (CryptoDataFetcher, "ticker"),
            "forex": (ForexDataFetcher, "symbol"),
            "vix": (VIXDataFetcher, None),
        }

        if market not in fetcher_factory:
            return json.dumps({"error": f"Unsupported market: {market}"})

        fetcher_class, symbol_param = fetcher_factory[market]
        market_dir = f"{output_dir}/{market}"

        # Create output directory
        Path(market_dir).mkdir(parents=True, exist_ok=True)

        successful_data = {}
        failed_symbols: List[str] = []
        files_saved = []

        # Use batch mode if supported
        if len(symbols) > 1 and market in ("us_stock", "tw_stock", "crypto"):
            logger.info(f"Using batch mode for {len(symbols)} symbols")

            fetcher_params = {
                symbol_param: "",  # Not used in batch mode
                "start_date": start_date,
                "end_date": end_date,
            }
            fetcher = fetcher_class(**fetcher_params)

            # Execute batch fetch in executor
            successful_data, failed_symbols = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: fetcher.fetch_batch(symbols),
            )

            logger.info(
                f"Batch fetch complete: {len(successful_data)} successful, "
                f"{len(failed_symbols)} failed"
            )

        else:
            # Single symbol mode
            for symbol in symbols:
                try:
                    logger.info(f"Fetching {symbol}...")

                    fetcher_params = {
                        "start_date": start_date,
                        "end_date": end_date,
                    }

                    if symbol_param:
                        fetcher_params[symbol_param] = symbol

                    fetcher = fetcher_class(**fetcher_params)

                    # Execute fetch in executor
                    df = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda f=fetcher: f.fetch(),
                    )

                    if df is not None and not df.empty:
                        successful_data[symbol] = df
                        logger.info(f"✓ {symbol}: {len(df)} rows")
                    else:
                        failed_symbols.append(symbol)
                        logger.info(f"✗ {symbol}: No data returned")

                except Exception as e:
                    failed_symbols.append(symbol)
                    logger.warning(f"Failed to fetch {symbol}: {e}")

        # Save all successful downloads
        file_manager = FileManager(base_data_dir=market_dir)

        for symbol, df in successful_data.items():
            try:
                actual_end_date = end_date or df.index[-1].strftime("%Y-%m-%d")
                filepath = file_manager.save_to_csv(
                    df=df,
                    ticker=symbol,
                    start_date=start_date,
                    end_date=actual_end_date,
                    overwrite=True,
                )
                files_saved.append(
                    {
                        "symbol": symbol,
                        "filepath": str(filepath),
                        "rows": len(df),
                    }
                )
                logger.info(f"Saved {symbol} to {Path(filepath).name}")
            except Exception as e:
                logger.error(f"Failed to save {symbol}: {e}")
                if symbol in successful_data:
                    failed_symbols.append(symbol)

        result = {
            "successful_symbols": list(successful_data.keys()),
            "failed_symbols": failed_symbols,
            "files_saved": files_saved,
            "total_symbols": len(symbols),
            "success_count": len(successful_data),
        }

        # Store file paths in context if provided
        if tool_context:
            tool_context.state["fetched_data_files"] = [f["filepath"] for f in files_saved]

        logger.info(f"Data fetch complete: {len(successful_data)} successful, {len(failed_symbols)} failed")
        return json.dumps(result, indent=2)

    except Exception as e:
        error_msg = f"Data fetch failed: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})
