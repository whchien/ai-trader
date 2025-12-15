"""Utility functions for running backtests with Backtrader.

This module provides helper functions to simplify common Backtrader operations
without the overhead of a wrapper class.
"""
import glob
import os
from pathlib import Path
from typing import List, Optional, Type, Union

import backtrader as bt
import pandas as pd

from ai_trader.backtesting.strategies.classic import NaiveSMAStrategy
from ai_trader.core.logging import get_logger
from ai_trader.core.utils import extract_ticker_from_path
from ai_trader.data.fetchers.base import load_example

logger = get_logger(__name__)


def create_cerebro(
    cash: float = 1000000,
    commission: float = 0.001425,
) -> bt.Cerebro:
    """
    Create and configure a Cerebro instance with broker settings.

    Args:
        cash: Initial cash amount
        commission: Commission rate (default: 0.001425 for Taiwan market)

    Returns:
        Configured Cerebro instance

    Example:
        >>> cerebro = create_cerebro(cash=100000, commission=0.001)
        >>> cerebro.broker.getvalue()
        100000.0
    """
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(cash)
    cerebro.broker.setcommission(commission=commission)
    logger.info(f"Created Cerebro: cash=${cash:,}, commission={commission:.4f}")
    return cerebro


def add_stock_data(
    cerebro: bt.Cerebro,
    source: Union[pd.DataFrame, str, Path, None] = None,
    name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    date_col: str = "date",
) -> None:
    """
    Add stock data to Cerebro instance.

    Args:
        cerebro: Cerebro instance to add data to
        source: DataFrame, file path, or None for example data
        name: Optional name for the data feed
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)
        date_col: Name of the date column in CSV

    Example:
        >>> cerebro = create_cerebro()
        >>> add_stock_data(cerebro, "data/AAPL.csv")
        >>> add_stock_data(cerebro, df, name="MSFT")
    """
    # Load data
    if source is None:
        df = load_example()
    elif isinstance(source, pd.DataFrame):
        df = source.copy()
    elif isinstance(source, (str, Path)):
        df = pd.read_csv(source, parse_dates=[date_col], index_col=[date_col])
    else:
        raise ValueError(f"Unsupported source type: {type(source)}")

    # Filter by date range
    if start_date or end_date:
        df = df[start_date:end_date]

    # Create data feed
    feed = bt.feeds.PandasData(
        dataname=df,
        openinterest=None,
        timeframe=bt.TimeFrame.Days,
    )

    # Add to cerebro
    if name:
        cerebro.adddata(feed, name=name)
    else:
        cerebro.adddata(feed)

    logger.info(f"Added stock data: {len(df)} rows" + (f" (name={name})" if name else ""))


def add_portfolio_data(
    cerebro: bt.Cerebro,
    data_dir: Union[str, Path],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    date_col: str = "date",
    pattern: str = "*.csv",
) -> None:
    """
    Load multiple stock files from a directory.

    Args:
        cerebro: Cerebro instance to add data to
        data_dir: Directory containing CSV files
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)
        date_col: Name of the date column in CSV
        pattern: File pattern to match (default: "*.csv")

    Example:
        >>> cerebro = create_cerebro()
        >>> add_portfolio_data(cerebro, "./data/tw_stock/")
    """
    data_dir = Path(data_dir)
    files = glob.glob(str(data_dir / pattern))

    if not files:
        raise ValueError(f"No files found in {data_dir} matching {pattern}")

    for file in files:
        df = pd.read_csv(file, parse_dates=[date_col], index_col=[date_col])

        # Filter by date range
        if start_date or end_date:
            df = df[start_date:end_date]

        # Extract ticker name from file path
        ticker = extract_ticker_from_path(file)

        # Create and add data feed
        data = bt.feeds.PandasData(
            dataname=df,
            name=ticker,
            timeframe=bt.TimeFrame.Days,
            plot=False,
        )
        cerebro.adddata(data, name=ticker)

    logger.info(f"Added portfolio data: {len(files)} stocks from {data_dir}")


def add_default_analyzers(cerebro: bt.Cerebro) -> None:
    """
    Add commonly used analyzers to Cerebro.

    Adds:
    - SharpeRatio
    - DrawDown
    - Returns

    Args:
        cerebro: Cerebro instance to add analyzers to

    Example:
        >>> cerebro = create_cerebro()
        >>> add_default_analyzers(cerebro)
    """
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
    cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
    logger.debug("Added default analyzers: sharpe, drawdown, returns")


def add_analyzers(
    cerebro: bt.Cerebro,
    analyzers: List[str],
) -> None:
    """
    Add specific analyzers to Cerebro by name.

    Args:
        cerebro: Cerebro instance to add analyzers to
        analyzers: List of analyzer names
                  Supported: 'sharpe', 'drawdown', 'returns', 'trades', 'sqn'

    Example:
        >>> cerebro = create_cerebro()
        >>> add_analyzers(cerebro, ['sharpe', 'drawdown', 'trades'])
    """
    analyzer_map = {
        "sharpe": bt.analyzers.SharpeRatio,
        "drawdown": bt.analyzers.DrawDown,
        "returns": bt.analyzers.Returns,
        "trades": bt.analyzers.TradeAnalyzer,
        "sqn": bt.analyzers.SQN,
    }

    for name in analyzers:
        if name in analyzer_map:
            cerebro.addanalyzer(analyzer_map[name], _name=name)
        else:
            logger.warning(f"Unknown analyzer: {name}")

    logger.debug(f"Added analyzers: {', '.join(analyzers)}")


def add_sizer(
    cerebro: bt.Cerebro,
    sizer_type: str = "percent",
    **sizer_params,
) -> None:
    """
    Add position sizer to Cerebro.

    Args:
        cerebro: Cerebro instance to add sizer to
        sizer_type: Type of sizer ('percent' or 'fixed')
        **sizer_params: Parameters for the sizer

    Example:
        >>> cerebro = create_cerebro()
        >>> add_sizer(cerebro, "percent", percents=90)
        >>> add_sizer(cerebro, "fixed", stake=100)
    """
    if sizer_type == "percent":
        percents = sizer_params.get("percents", 95)
        cerebro.addsizer(bt.sizers.PercentSizer, percents=percents)
        logger.debug(f"Added PercentSizer: {percents}%")
    elif sizer_type == "fixed":
        stake = sizer_params.get("stake", 10)
        cerebro.addsizer(bt.sizers.FixedSize, stake=stake)
        logger.debug(f"Added FixedSize sizer: stake={stake}")
    else:
        raise ValueError(f"Unknown sizer type: {sizer_type}")


def print_results(
    results: List[bt.Strategy],
    initial_value: float,
    final_value: float,
) -> None:
    """
    Print backtest results in a formatted way.

    Args:
        results: List of strategy instances from cerebro.run()
        initial_value: Initial portfolio value
        final_value: Final portfolio value

    Example:
        >>> results = cerebro.run()
        >>> print_results(results, cerebro.broker.startingcash, cerebro.broker.getvalue())
    """
    print("\n" + "=" * 60)
    print("BACKTEST RESULTS")
    print("=" * 60)

    # Portfolio values
    print(f"\nInitial Value: ${initial_value:,.2f}")
    print(f"Final Value:   ${final_value:,.2f}")
    print(f"Profit/Loss:   ${final_value - initial_value:+,.2f}")
    print(f"Return:        {(final_value / initial_value - 1) * 100:+.2f}%")

    # Analyzer results
    if results and len(results) > 0:
        strat = results[0]

        # Sharpe Ratio
        if hasattr(strat.analyzers, "sharpe"):
            sharpe = strat.analyzers.sharpe.get_analysis().get("sharperatio")
            if sharpe:
                print(f"\nSharpe Ratio:  {sharpe:.2f}")

        # Returns
        if hasattr(strat.analyzers, "returns"):
            returns = strat.analyzers.returns.get_analysis()
            if "rtot" in returns:
                print(f"Total Return:  {returns['rtot'] * 100:.2f}%")
            if "rnorm" in returns:
                print(f"Norm. Return:  {returns['rnorm'] * 100:.2f}%")

        # Drawdown
        if hasattr(strat.analyzers, "drawdown"):
            dd = strat.analyzers.drawdown.get_analysis()
            if "max" in dd and "drawdown" in dd["max"]:
                print(f"Max Drawdown:  {dd['max']['drawdown']:.2f}%")

        # Trade Analysis
        if hasattr(strat.analyzers, "trades"):
            trades = strat.analyzers.trades.get_analysis()
            total_trades = trades.get("total", {}).get("total", 0)
            if total_trades > 0:
                print(f"\nTotal Trades:  {total_trades}")
                won = trades.get("won", {}).get("total", 0)
                lost = trades.get("lost", {}).get("total", 0)
                print(f"Won:           {won}")
                print(f"Lost:          {lost}")
                if total_trades > 0:
                    win_rate = (won / total_trades) * 100
                    print(f"Win Rate:      {win_rate:.1f}%")

    print("=" * 60 + "\n")


def run_backtest(
    strategy: Type[bt.Strategy],
    data_source: Union[pd.DataFrame, str, Path, None] = None,
    cash: float = 1000000,
    commission: float = 0.001425,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sizer_type: str = "percent",
    sizer_params: Optional[dict] = None,
    analyzers: Optional[List[str]] = None,
    strategy_params: Optional[dict] = None,
    print_output: bool = True,
    plot: bool = False,
    plot_params: Optional[dict] = None,
) -> List[bt.Strategy]:
    """
    Run a complete backtest with sensible defaults.

    This is a convenience function that combines all setup steps.

    Args:
        strategy: Strategy class to run
        data_source: DataFrame, file path, or None for example
        cash: Initial cash amount
        commission: Commission rate
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)
        sizer_type: Type of sizer ('percent' or 'fixed')
        sizer_params: Parameters for sizer (e.g., {'percents': 90})
        analyzers: List of analyzer names (None for defaults)
        strategy_params: Parameters to pass to strategy (e.g., {'period': 20})
        print_output: Whether to print results (default: True)
        plot: Whether to plot results using cerebro.plot() (default: False)
        plot_params: Optional parameters to pass to cerebro.plot() (e.g., {'iplot': False})

    Returns:
        List of strategy instances with results

    Example:
        >>> from ai_trader.backtesting.strategies.classic.sma import SMAStrategy
        >>> results = run_backtest(
        ...     SMAStrategy,
        ...     "data/AAPL.csv",
        ...     cash=100000,
        ...     strategy_params={'fast_period': 10, 'slow_period': 30},
        ...     plot=True
        ... )
    """
    # Create cerebro
    cerebro = create_cerebro(cash=cash, commission=commission)

    # Add data
    add_stock_data(
        cerebro,
        source=data_source,
        start_date=start_date,
        end_date=end_date,
    )

    # Add strategy
    if strategy_params:
        cerebro.addstrategy(strategy, **strategy_params)
    else:
        cerebro.addstrategy(strategy)

    # Add sizer
    if sizer_params is None:
        sizer_params = {}
    add_sizer(cerebro, sizer_type, **sizer_params)

    # Add analyzers
    if analyzers is None:
        add_default_analyzers(cerebro)
    else:
        add_analyzers(cerebro, analyzers)

    # Get initial value
    initial_value = cerebro.broker.getvalue()

    # Run backtest
    logger.info(f"Running backtest with {strategy.__name__}")
    logger.info(f"Starting portfolio value: ${initial_value:,.2f}")

    results = cerebro.run()

    # Get final value
    final_value = cerebro.broker.getvalue()
    logger.info(f"Final portfolio value: ${final_value:,.2f}")

    # Print results
    if print_output:
        print_results(results, initial_value, final_value)

    # Plot results
    if plot:
        if plot_params is None:
            plot_params = {}
        logger.info("Generating backtest plot")
        cerebro.plot(**plot_params)

    return results