"""Utility functions for the trading backtester."""

import importlib
import inspect
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

import backtrader as bt
import pandas as pd

logger = logging.getLogger(__name__)


def get_available_strategies() -> Dict[str, Dict[str, Any]]:
    """Get all available trading strategies from ai_trader.
    
    Returns:
        Dictionary mapping strategy names to their metadata
    """
    try:
        # Import ai_trader modules
        import ai_trader.backtesting.strategies.classic as classic
        import ai_trader.backtesting.strategies.portfolio as portfolio
        
        strategies = {}
        
        # Get classic strategies
        classic_strategies = _get_strategies_from_module(classic)
        for name, cls in classic_strategies:
            strategies[name] = {
                "class": cls,
                "type": "classic",
                "description": _get_strategy_description(cls),
                "parameters": _get_strategy_parameters(cls),
                "module": cls.__module__,
            }
        
        # Get portfolio strategies
        portfolio_strategies = _get_strategies_from_module(portfolio)
        for name, cls in portfolio_strategies:
            strategies[name] = {
                "class": cls,
                "type": "portfolio", 
                "description": _get_strategy_description(cls),
                "parameters": _get_strategy_parameters(cls),
                "module": cls.__module__,
            }
        
        return strategies
        
    except ImportError as e:
        logger.error(f"Failed to import ai_trader strategies: {e}")
        return {}


def _get_strategies_from_module(module) -> List[tuple]:
    """Get all strategy classes from a module."""
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


def _get_strategy_description(strategy_class: Type[bt.Strategy]) -> str:
    """Extract description from strategy docstring."""
    if strategy_class.__doc__:
        return strategy_class.__doc__.split("\n")[0].strip()
    return "No description available"


def _get_strategy_parameters(strategy_class: Type[bt.Strategy]) -> Dict[str, Any]:
    """Extract parameters from strategy class."""
    params = {}
    if hasattr(strategy_class, "params"):
        for param_name in dir(strategy_class.params):
            if not param_name.startswith("_"):
                param_value = getattr(strategy_class.params, param_name)
                params[param_name] = param_value
    return params


def load_strategy_class(strategy_name: str) -> Optional[Type[bt.Strategy]]:
    """Load a strategy class by name.
    
    Args:
        strategy_name: Name of the strategy class
        
    Returns:
        Strategy class or None if not found
    """
    strategies = get_available_strategies()
    if strategy_name in strategies:
        return strategies[strategy_name]["class"]
    return None


def validate_date_range(start_date: Optional[str], end_date: Optional[str]) -> tuple:
    """Validate and normalize date range.
    
    Args:
        start_date: Start date string (YYYY-MM-DD) or None
        end_date: End date string (YYYY-MM-DD) or None
        
    Returns:
        Tuple of (start_date, end_date) as strings
    """
    if start_date is None:
        # Default to 2 years ago
        start_date = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
    
    if end_date is None:
        # Default to today
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    # Validate format
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError as e:
        raise ValueError(f"Invalid date format. Use YYYY-MM-DD: {e}")
    
    return start_date, end_date


def extract_performance_metrics(backtest_results: List[bt.Strategy]) -> Dict[str, Any]:
    """Extract key performance metrics from backtest results.
    
    Args:
        backtest_results: Results from cerebro.run()
        
    Returns:
        Dictionary of performance metrics
    """
    if not backtest_results:
        return {}
    
    strat = backtest_results[0]
    metrics = {}
    
    # Basic metrics
    if hasattr(strat.analyzers, "returns"):
        returns = strat.analyzers.returns.get_analysis()
        metrics.update({
            "total_return": returns.get("rtot", 0) * 100,
            "normalized_return": returns.get("rnorm", 0) * 100,
        })
    
    # Sharpe ratio
    if hasattr(strat.analyzers, "sharpe"):
        sharpe = strat.analyzers.sharpe.get_analysis().get("sharperatio")
        metrics["sharpe_ratio"] = sharpe if sharpe else 0
    
    # Drawdown
    if hasattr(strat.analyzers, "drawdown"):
        dd = strat.analyzers.drawdown.get_analysis()
        metrics.update({
            "max_drawdown": dd.get("max", {}).get("drawdown", 0),
            "max_drawdown_length": dd.get("max", {}).get("len", 0),
        })
    
    # Trade analysis
    if hasattr(strat.analyzers, "trades"):
        trades = strat.analyzers.trades.get_analysis()
        total_trades = trades.get("total", {}).get("total", 0)
        won_trades = trades.get("won", {}).get("total", 0)
        
        metrics.update({
            "total_trades": total_trades,
            "winning_trades": won_trades,
            "losing_trades": trades.get("lost", {}).get("total", 0),
            "win_rate": (won_trades / total_trades * 100) if total_trades > 0 else 0,
        })
    
    return metrics


def format_performance_summary(metrics: Dict[str, Any]) -> str:
    """Format performance metrics into a readable summary.
    
    Args:
        metrics: Performance metrics dictionary
        
    Returns:
        Formatted summary string
    """
    if not metrics:
        return "No performance metrics available"
    
    summary_parts = []
    
    # Returns
    if "total_return" in metrics:
        summary_parts.append(f"Total Return: {metrics['total_return']:.2f}%")
    
    # Sharpe ratio
    if "sharpe_ratio" in metrics:
        summary_parts.append(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    
    # Max drawdown
    if "max_drawdown" in metrics:
        summary_parts.append(f"Max Drawdown: {metrics['max_drawdown']:.2f}%")
    
    # Win rate
    if "win_rate" in metrics:
        summary_parts.append(f"Win Rate: {metrics['win_rate']:.1f}%")
    
    # Total trades
    if "total_trades" in metrics:
        summary_parts.append(f"Total Trades: {metrics['total_trades']}")
    
    return " | ".join(summary_parts)


def generate_parameter_grid(parameter_ranges: Dict[str, List]) -> List[Dict[str, Any]]:
    """Generate all combinations of parameters for grid search.
    
    Args:
        parameter_ranges: Dictionary mapping parameter names to lists of values
        
    Returns:
        List of parameter combinations
    """
    import itertools
    
    if not parameter_ranges:
        return [{}]
    
    keys = list(parameter_ranges.keys())
    values = list(parameter_ranges.values())
    
    combinations = []
    for combination in itertools.product(*values):
        param_dict = dict(zip(keys, combination))
        combinations.append(param_dict)
    
    return combinations


def safe_json_serialize(obj: Any) -> str:
    """Safely serialize object to JSON, handling non-serializable types.
    
    Args:
        obj: Object to serialize
        
    Returns:
        JSON string
    """
    def default_serializer(o):
        if isinstance(o, (pd.Timestamp, datetime)):
            return o.isoformat()
        elif isinstance(o, pd.DataFrame):
            return o.to_dict()
        elif hasattr(o, "__dict__"):
            return str(o)
        else:
            return str(o)
    
    return json.dumps(obj, default=default_serializer, indent=2)


def create_results_directory(base_dir: str = "results") -> Path:
    """Create a timestamped results directory.
    
    Args:
        base_dir: Base directory name
        
    Returns:
        Path to created directory
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path(base_dir) / f"backtest_{timestamp}"
    results_dir.mkdir(parents=True, exist_ok=True)
    return results_dir