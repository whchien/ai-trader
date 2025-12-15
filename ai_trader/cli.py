"""Command-line interface for ai-trader."""
import importlib
import sys
from pathlib import Path
from typing import Optional

import click
import yaml

from ai_trader.core.logging import get_logger
from ai_trader.utils.backtest import (
    add_analyzers,
    add_portfolio_data,
    add_sizer,
    add_stock_data,
    create_cerebro,
    print_results,
)

logger = get_logger(__name__)


@click.group()
@click.version_option(version="0.2.0")
def cli():
    """AI Trader - Backtesting framework for algorithmic trading strategies."""
    pass


@cli.command()
@click.argument("config_file", type=click.Path(exists=True))
@click.option("--strategy", help="Override strategy from config")
@click.option("--cash", type=float, help="Override initial cash")
@click.option("--commission", type=float, help="Override commission rate")
def run(
    config_file: str,
    strategy: Optional[str],
    cash: Optional[float],
    commission: Optional[float],
):
    """
    Run a backtest from a YAML configuration file.

    Example:
        ai-trader run config/backtest/sma.yaml
        ai-trader run config/backtest/portfolio.yaml --cash 500000
    """
    # Load config
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    # Apply overrides
    if strategy:
        config["strategy"]["class"] = strategy
    if cash is not None:
        config["broker"]["cash"] = cash
    if commission is not None:
        config["broker"]["commission"] = commission

    # Create cerebro
    cerebro = create_cerebro(
        cash=config["broker"]["cash"],
        commission=config["broker"]["commission"],
    )

    # Load data
    data_config = config.get("data", {})
    if "file" in data_config:
        # Single stock
        add_stock_data(
            cerebro,
            source=data_config["file"],
            start_date=data_config.get("start_date"),
            end_date=data_config.get("end_date"),
            date_col=data_config.get("date_col", "date"),
        )
    elif "directory" in data_config:
        # Portfolio
        add_portfolio_data(
            cerebro,
            data_dir=data_config["directory"],
            start_date=data_config.get("start_date"),
            end_date=data_config.get("end_date"),
            date_col=data_config.get("date_col", "date"),
        )
    else:
        click.echo("Error: Config must specify either 'data.file' or 'data.directory'", err=True)
        sys.exit(1)

    # Load strategy class
    strategy_config = config["strategy"]
    strategy_class = _load_strategy_class(strategy_config["class"])

    # Add strategy with parameters
    strategy_params = strategy_config.get("params", {})
    cerebro.addstrategy(strategy_class, **strategy_params)

    # Add sizer
    sizer_config = config.get("sizer", {"type": "percent", "params": {"percents": 95}})
    add_sizer(cerebro, sizer_config["type"], **sizer_config.get("params", {}))

    # Add analyzers
    analyzer_list = config.get("analyzers", ["sharpe", "drawdown", "returns"])
    add_analyzers(cerebro, analyzer_list)

    # Get initial value
    initial_value = cerebro.broker.getvalue()

    # Run backtest
    click.echo(f"\nRunning backtest: {strategy_class.__name__}")
    click.echo(f"Data: {data_config.get('file') or data_config.get('directory')}")
    click.echo(f"Initial value: ${initial_value:,.2f}\n")

    results = cerebro.run()

    # Get final value
    final_value = cerebro.broker.getvalue()

    # Print results
    print_results(results, initial_value, final_value)


@cli.command()
@click.option(
    "--type",
    "strategy_type",
    type=click.Choice(["classic", "portfolio", "all"]),
    default="all",
    help="Type of strategies to list",
)
def list_strategies(strategy_type: str):
    """
    List available trading strategies.

    Example:
        ai-trader list-strategies
        ai-trader list-strategies --type classic
    """
    from ai_trader.backtesting.strategies import classic, portfolio

    click.echo("\n" + "=" * 60)
    click.echo("AVAILABLE STRATEGIES")
    click.echo("=" * 60 + "\n")

    if strategy_type in ("classic", "all"):
        click.echo("Classic Strategies (single stock):")
        click.echo("-" * 40)
        classic_strategies = _get_strategies_from_module(classic)
        for name, cls in classic_strategies:
            doc = cls.__doc__.split("\n")[0] if cls.__doc__ else "No description"
            click.echo(f"  • {name:30s} - {doc}")
        click.echo()

    if strategy_type in ("portfolio", "all"):
        click.echo("Portfolio Strategies (multi-stock):")
        click.echo("-" * 40)
        portfolio_strategies = _get_strategies_from_module(portfolio)
        for name, cls in portfolio_strategies:
            doc = cls.__doc__.split("\n")[0] if cls.__doc__ else "No description"
            click.echo(f"  • {name:30s} - {doc}")
        click.echo()


@cli.command()
@click.argument("symbols", nargs=-1, required=False)
@click.option("--symbols-file", type=click.Path(exists=True), help="File containing symbols (one per line)")
@click.option("--market", type=click.Choice(["us", "tw", "crypto", "forex", "vix"]), default="us")
@click.option("--start-date", required=True, help="Start date (YYYY-MM-DD)")
@click.option("--end-date", help="End date (YYYY-MM-DD), defaults to today")
@click.option("--output-dir", help="Output directory", default="./data")
def fetch(
    symbols: tuple[str],
    symbols_file: Optional[str],
    market: str,
    start_date: str,
    end_date: Optional[str],
    output_dir: str,
):
    """
    Fetch market data and save to CSV.

    Supports multiple input methods:
    - Space-separated symbols: ai-trader fetch AAPL MSFT GOOGL --market us --start-date 2020-01-01
    - Comma-separated symbols: ai-trader fetch AAPL,MSFT,GOOGL --market us --start-date 2020-01-01
    - From file: ai-trader fetch --symbols-file symbols.txt --market us --start-date 2020-01-01
    - Single symbol (backward compatible): ai-trader fetch AAPL --market us --start-date 2020-01-01

    Example:
        ai-trader fetch AAPL --market us --start-date 2020-01-01
        ai-trader fetch AAPL MSFT GOOGL --market us --start-date 2020-01-01
        ai-trader fetch 2330 2317 2454 --market tw --start-date 2020-01-01
        ai-trader fetch BTC-USD ETH-USD SOL-USD --market crypto --start-date 2020-01-01
        ai-trader fetch --symbols-file symbols.txt --market us --start-date 2020-01-01
    """
    from ai_trader.data.fetchers import (
        CryptoDataFetcher,
        ForexDataFetcher,
        TWStockFetcher,
        USStockFetcher,
        VIXDataFetcher,
    )
    from ai_trader.data.storage import FileManager

    # Parse and collect symbols from multiple sources
    symbol_list = []

    # From command-line arguments (space-separated and comma-separated)
    if symbols:
        for sym in symbols:
            # Handle comma-separated within single argument
            symbol_list.extend(s.strip() for s in sym.split(',') if s.strip())

    # From file
    if symbols_file:
        if symbols:
            click.echo("✗ Error: Cannot specify both symbol arguments and --symbols-file", err=True)
            sys.exit(1)
        with open(symbols_file) as f:
            symbol_list.extend(line.strip() for line in f if line.strip())

    # Validate we have at least one symbol
    if not symbol_list:
        click.echo("✗ Error: No symbols provided. Use symbol arguments or --symbols-file", err=True)
        click.echo("\nExamples:")
        click.echo("  ai-trader fetch AAPL --market us --start-date 2020-01-01")
        click.echo("  ai-trader fetch AAPL MSFT GOOGL --market us --start-date 2020-01-01")
        click.echo("  ai-trader fetch --symbols-file symbols.txt --market us --start-date 2020-01-01")
        sys.exit(1)

    # Remove duplicates while preserving order
    seen = set()
    symbol_list = [s for s in symbol_list if not (s in seen or seen.add(s))]

    # Display summary
    click.echo(f"\nFetching {market.upper()} market data for {len(symbol_list)} symbol(s)...")
    click.echo(f"Symbols: {', '.join(symbol_list)}")
    click.echo(f"Date range: {start_date} to {end_date or 'today'}\n")

    # Create market-specific subdirectory
    if market == "us":
        market_dir = f"{output_dir}/us_stock"
    elif market == "tw":
        market_dir = f"{output_dir}/tw_stock"
    elif market == "crypto":
        market_dir = f"{output_dir}/crypto"
    elif market == "forex":
        market_dir = f"{output_dir}/forex"
    elif market == "vix":
        market_dir = f"{output_dir}/vix"
    else:
        market_dir = output_dir

    try:
        # Handle batch vs single symbol
        if len(symbol_list) == 1 or market in ("forex", "vix"):
            # Single symbol or markets that don't support batch - use original logic
            symbol = symbol_list[0]

            if market == "us":
                fetcher = USStockFetcher(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date
                )
            elif market == "tw":
                fetcher = TWStockFetcher(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date
                )
            elif market == "crypto":
                fetcher = CryptoDataFetcher(
                    ticker=symbol,
                    start_date=start_date,
                    end_date=end_date
                )
            elif market == "forex":
                fetcher = ForexDataFetcher(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date
                )
            elif market == "vix":
                fetcher = VIXDataFetcher(
                    start_date=start_date,
                    end_date=end_date
                )
            else:
                click.echo(f"✗ Invalid market: {market}", err=True)
                sys.exit(1)

            # Fetch data
            df = fetcher.fetch()

            if df is None or df.empty:
                click.echo("✗ No data returned", err=True)
                sys.exit(1)

            # Save using FileManager
            file_manager = FileManager(base_data_dir=market_dir)
            actual_end_date = end_date or df.index[-1].strftime("%Y-%m-%d")

            filepath = file_manager.save_to_csv(
                df=df,
                ticker=symbol,
                start_date=start_date,
                end_date=actual_end_date,
                overwrite=True
            )

            click.echo(f"✓ Data saved to {filepath}")
            click.echo(f"  Rows: {len(df)}")
            click.echo(f"  Columns: {', '.join(df.columns)}")
            click.echo(f"  Date range: {df.index[0]} to {df.index[-1]}")

        else:
            # Batch mode for US/TW stocks and crypto
            if market == "us":
                fetcher = USStockFetcher(
                    symbol="",  # Not used in batch mode
                    start_date=start_date,
                    end_date=end_date
                )
                successful_data, failed_symbols = fetcher.fetch_batch(symbol_list)
            elif market == "tw":
                fetcher = TWStockFetcher(
                    symbol="",  # Not used in batch mode
                    start_date=start_date,
                    end_date=end_date
                )
                successful_data, failed_symbols = fetcher.fetch_batch(symbol_list)
            elif market == "crypto":
                fetcher = CryptoDataFetcher(
                    ticker="",  # Not used in batch mode
                    start_date=start_date,
                    end_date=end_date
                )
                successful_data, failed_symbols = fetcher.fetch_batch(symbol_list)
            else:
                click.echo(f"✗ Batch mode not supported for market: {market}", err=True)
                sys.exit(1)

            # Save all successful downloads
            file_manager = FileManager(base_data_dir=market_dir)
            saved_files = []

            for symbol, df in successful_data.items():
                actual_end_date = end_date or df.index[-1].strftime("%Y-%m-%d")
                filepath = file_manager.save_to_csv(
                    df=df,
                    ticker=symbol,
                    start_date=start_date,
                    end_date=actual_end_date,
                    overwrite=True
                )
                saved_files.append((symbol, filepath, len(df)))

            # Display summary
            if saved_files:
                click.echo(f"\n✓ Successfully downloaded {len(saved_files)}/{len(symbol_list)} symbols:")
                for symbol, filepath, rows in saved_files:
                    click.echo(f"  • {symbol}: {rows} rows → {Path(filepath).name}")

            if failed_symbols:
                click.echo(f"\n✗ Failed to download {len(failed_symbols)} symbol(s):")
                for symbol in failed_symbols:
                    click.echo(f"  • {symbol}")
                sys.exit(1)

            if not saved_files:
                click.echo("\n✗ No symbols were successfully downloaded", err=True)
                sys.exit(1)

    except Exception as e:
        click.echo(f"\n✗ Failed to fetch data: {e}", err=True)
        logger.exception("Error in fetch command")
        sys.exit(1)


@cli.command()
@click.argument("strategy_name")
@click.argument("data_file")
@click.option("--cash", type=float, default=1000000, help="Initial cash")
@click.option("--commission", type=float, default=0.001425, help="Commission rate")
@click.option("--start-date", help="Start date (YYYY-MM-DD)")
@click.option("--end-date", help="End date (YYYY-MM-DD)")
def quick(
    strategy_name: str,
    data_file: str,
    cash: float,
    commission: float,
    start_date: Optional[str],
    end_date: Optional[str],
):
    """
    Quick backtest without config file.

    Example:
        ai-trader quick SMAStrategy data/AAPL.csv
        ai-trader quick BBandsStrategy data/AAPL.csv --cash 50000
    """
    # Load strategy class
    strategy_class = _load_strategy_class(strategy_name)

    # Create cerebro
    cerebro = create_cerebro(cash=cash, commission=commission)

    # Add data
    add_stock_data(cerebro, source=data_file, start_date=start_date, end_date=end_date)

    # Add strategy
    cerebro.addstrategy(strategy_class)

    # Add sizer and analyzers
    add_sizer(cerebro, "percent", percents=95)
    add_analyzers(cerebro, ["sharpe", "drawdown", "returns"])

    # Get initial value
    initial_value = cerebro.broker.getvalue()

    # Run backtest
    click.echo(f"\nRunning quick backtest: {strategy_class.__name__}")
    click.echo(f"Data: {data_file}")
    click.echo(f"Initial value: ${initial_value:,.2f}\n")

    results = cerebro.run()

    # Get final value
    final_value = cerebro.broker.getvalue()

    # Print results
    print_results(results, initial_value, final_value)


def _load_strategy_class(class_path: str):
    """
    Load a strategy class from a string path.

    Args:
        class_path: Full path like "ai_trader.backtesting.strategies.classic.sma.SMAStrategy"
                   or short name like "SMAStrategy"

    Returns:
        Strategy class
    """
    # If it's a short name, try to find it in classic or portfolio
    if "." not in class_path:
        # Try to import from classic module (searches __init__.py exports)
        try:
            from ai_trader.backtesting.strategies import classic
            if hasattr(classic, class_path):
                return getattr(classic, class_path)
        except (ImportError, AttributeError):
            pass

        # Try to import from portfolio module (searches __init__.py exports)
        try:
            from ai_trader.backtesting.strategies import portfolio
            if hasattr(portfolio, class_path):
                return getattr(portfolio, class_path)
        except (ImportError, AttributeError):
            pass

        raise ValueError(f"Strategy not found: {class_path}")

    # Full path provided
    module_path, class_name = class_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def _get_strategies_from_module(module):
    """Get all strategy classes from a module."""
    import inspect
    import backtrader as bt

    strategies = []
    for name, obj in inspect.getmembers(module):
        if (
            inspect.isclass(obj)
            and issubclass(obj, bt.Strategy)
            and obj is not bt.Strategy
            and not name.startswith("_")
        ):
            strategies.append((name, obj))
    return sorted(strategies, key=lambda x: x[0])


if __name__ == "__main__":
    cli()
