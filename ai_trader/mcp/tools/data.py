"""MCP tools for fetching market data."""

import asyncio
from pathlib import Path
from typing import List

from fastmcp import Context

from ai_trader.core.logging import get_logger
from ai_trader.data.fetchers import (
    CryptoDataFetcher,
    ForexDataFetcher,
    TWStockFetcher,
    USStockFetcher,
    VIXDataFetcher,
)
from ai_trader.data.storage import FileManager
from ai_trader.mcp.models import FetchDataRequest, FetchResult, FetchedSymbol

logger = get_logger(__name__)


async def fetch_data_tool(
    request: FetchDataRequest,
    ctx: Context,
) -> FetchResult:
    """
    Fetch market data and save to CSV files.

    Supports US stocks, Taiwan stocks, cryptocurrencies, forex, and VIX index.
    Can fetch multiple symbols in batch mode.
    """
    try:
        await ctx.info(
            f"Fetching {len(request.symbols)} symbol(s) from {request.market} market"
        )

        # Factory mapping for fetcher classes
        fetcher_factory = {
            "us_stock": (USStockFetcher, "symbol"),
            "tw_stock": (TWStockFetcher, "symbol"),
            "crypto": (CryptoDataFetcher, "ticker"),
            "forex": (ForexDataFetcher, "symbol"),
            "vix": (VIXDataFetcher, None),
        }

        if request.market not in fetcher_factory:
            raise ValueError(f"Unsupported market: {request.market}")

        fetcher_class, symbol_param = fetcher_factory[request.market]
        market_dir = f"{request.output_dir}/{request.market}"

        # Create output directory
        Path(market_dir).mkdir(parents=True, exist_ok=True)

        successful_data = {}
        failed_symbols: List[str] = []
        files_saved: List[FetchedSymbol] = []

        # Use batch mode if supported
        if len(request.symbols) > 1 and request.market in ("us_stock", "tw_stock", "crypto"):
            await ctx.info(f"Using batch mode for {len(request.symbols)} symbols")

            fetcher_params = {
                symbol_param: "",  # Not used in batch mode
                "start_date": request.start_date,
                "end_date": request.end_date,
            }
            fetcher = fetcher_class(**fetcher_params)

            # Execute batch fetch in executor
            successful_data, failed_symbols = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: fetcher.fetch_batch(request.symbols),
            )

            await ctx.info(
                f"Batch fetch complete: {len(successful_data)} successful, "
                f"{len(failed_symbols)} failed"
            )

        else:
            # Single symbol mode
            for symbol in request.symbols:
                try:
                    await ctx.info(f"Fetching {symbol}...")

                    fetcher_params = {
                        "start_date": request.start_date,
                        "end_date": request.end_date,
                    }

                    if symbol_param:
                        fetcher_params[symbol_param] = symbol

                    fetcher = fetcher_class(**fetcher_params)

                    # Execute fetch in executor
                    df = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: fetcher.fetch(),
                    )

                    if df is not None and not df.empty:
                        successful_data[symbol] = df
                        await ctx.info(f"✓ {symbol}: {len(df)} rows")
                    else:
                        failed_symbols.append(symbol)
                        await ctx.info(f"✗ {symbol}: No data returned")

                except Exception as e:
                    failed_symbols.append(symbol)
                    error_msg = f"✗ {symbol}: {str(e)}"
                    await ctx.info(error_msg)
                    logger.warning(f"Failed to fetch {symbol}: {e}")

        # Save all successful downloads
        file_manager = FileManager(base_data_dir=market_dir)

        for symbol, df in successful_data.items():
            try:
                actual_end_date = request.end_date or df.index[-1].strftime("%Y-%m-%d")
                filepath = file_manager.save_to_csv(
                    df=df,
                    ticker=symbol,
                    start_date=request.start_date,
                    end_date=actual_end_date,
                    overwrite=True,
                )
                files_saved.append(
                    FetchedSymbol(
                        symbol=symbol,
                        filepath=str(filepath),
                        rows=len(df),
                    )
                )
                await ctx.info(f"Saved {symbol} to {Path(filepath).name}")
            except Exception as e:
                logger.error(f"Failed to save {symbol}: {e}")
                if symbol in successful_data:
                    failed_symbols.append(symbol)

        return FetchResult(
            successful_symbols=list(successful_data.keys()),
            failed_symbols=failed_symbols,
            files_saved=files_saved,
            total_symbols=len(request.symbols),
            success_count=len(successful_data),
        )

    except Exception as e:
        error_msg = f"Data fetch failed: {str(e)}"
        await ctx.error(error_msg)
        logger.exception("Error in fetch_data_tool")
        raise
