"""Tools for the Root Coordinator Agent."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from google.adk.tools import ToolContext

from ..core.utils import get_available_strategies as _get_available_strategies

logger = logging.getLogger(__name__)


async def get_available_strategies(
    strategy_type: Optional[str] = None,
    tool_context: ToolContext = None,
) -> str:
    """Get list of available trading strategies.

    Args:
        strategy_type: Filter by strategy type ('classic', 'portfolio', or None for all)
        tool_context: Tool context for state management

    Returns:
        JSON string with available strategies and their metadata
    """
    logger.info(f"Getting available strategies (type: {strategy_type})")

    try:
        all_strategies = _get_available_strategies()

        # Filter by type if specified
        if strategy_type:
            filtered_strategies = {
                name: info for name, info in all_strategies.items() if info["type"] == strategy_type
            }
        else:
            filtered_strategies = all_strategies

        # Prepare response with strategy summaries
        strategy_summaries = {}
        for name, info in filtered_strategies.items():
            strategy_summaries[name] = {
                "type": info["type"],
                "description": info["description"],
                "parameters": list(info["parameters"].keys()),
                "parameter_defaults": info["parameters"],
            }

        result = {
            "total_strategies": len(strategy_summaries),
            "strategy_type_filter": strategy_type,
            "strategies": strategy_summaries,
        }

        # Store in context for other agents
        if tool_context:
            tool_context.state["available_strategies"] = all_strategies
            tool_context.state["filtered_strategies"] = filtered_strategies

        logger.info(f"Found {len(strategy_summaries)} strategies")
        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error getting available strategies: {e}")
        return json.dumps({"error": str(e)})


async def get_market_data_summary(
    symbol: str,
    period: str = "1y",
    tool_context: ToolContext = None,
) -> str:
    """Get a quick summary of market data for a symbol.

    Args:
        symbol: Stock symbol (e.g., 'AAPL', 'MSFT')
        period: Time period ('1y', '2y', '5y', 'max')
        tool_context: Tool context for state management

    Returns:
        JSON string with market data summary
    """
    logger.info(f"Getting market data summary for {symbol} ({period})")

    try:
        # Import ai_trader data fetcher
        import ai_trader.data.fetchers.base as base_fetcher

        MarketDataFetcher = base_fetcher.MarketDataFetcher

        # Determine start year based on period
        current_year = datetime.now().year
        period_map = {
            "1y": current_year - 1,
            "2y": current_year - 2,
            "5y": current_year - 5,
            "max": 2010,  # Default to 2010 for max
        }
        start_year = period_map.get(period, current_year - 1)

        # Fetch data
        fetcher = MarketDataFetcher(market="us", start_year=start_year)
        df = fetcher.fetch_data(symbol)

        if df is None or df.empty:
            return json.dumps({"error": f"No data found for symbol {symbol}"})

        # Calculate summary statistics
        latest_price = df["Close"].iloc[-1]
        price_change = df["Close"].iloc[-1] - df["Close"].iloc[0]
        price_change_pct = (price_change / df["Close"].iloc[0]) * 100

        volatility = df["Close"].pct_change().std() * (252**0.5) * 100  # Annualized
        avg_volume = df["Volume"].mean()

        summary = {
            "symbol": symbol,
            "period": period,
            "data_points": len(df),
            "date_range": {
                "start": df.index[0].strftime("%Y-%m-%d"),
                "end": df.index[-1].strftime("%Y-%m-%d"),
            },
            "price_info": {
                "latest_price": round(latest_price, 2),
                "period_change": round(price_change, 2),
                "period_change_pct": round(price_change_pct, 2),
                "price_range": {
                    "high": round(df["High"].max(), 2),
                    "low": round(df["Low"].min(), 2),
                },
            },
            "statistics": {
                "annualized_volatility_pct": round(volatility, 2),
                "average_daily_volume": int(avg_volume),
            },
        }

        # Store data in context for other agents
        if tool_context:
            tool_context.state[f"market_data_{symbol}"] = df
            tool_context.state[f"market_summary_{symbol}"] = summary

        logger.info(f"Market data summary generated for {symbol}")
        return json.dumps(summary, indent=2)

    except Exception as e:
        logger.error(f"Error getting market data summary for {symbol}: {e}")
        return json.dumps({"error": str(e)})


async def save_session_state(
    session_name: str,
    tool_context: ToolContext,
) -> str:
    """Save current session state to file.

    Args:
        session_name: Name for the saved session
        tool_context: Tool context containing state to save

    Returns:
        JSON string with save status
    """
    logger.info(f"Saving session state: {session_name}")

    try:
        # Create sessions directory
        sessions_dir = Path("sessions")
        sessions_dir.mkdir(exist_ok=True)

        # Prepare state data (exclude non-serializable objects)
        state_data = {}
        for key, value in tool_context.state.items():
            try:
                # Test if value is JSON serializable
                json.dumps(value)
                state_data[key] = value
            except (TypeError, ValueError):
                # Store string representation for non-serializable objects
                state_data[key] = str(value)

        # Add metadata
        session_data = {
            "session_name": session_name,
            "timestamp": datetime.now().isoformat(),
            "state": state_data,
        }

        # Save to file
        session_file = sessions_dir / f"{session_name}.json"
        with open(session_file, "w") as f:
            json.dump(session_data, f, indent=2)

        result = {
            "status": "success",
            "session_name": session_name,
            "file_path": str(session_file),
            "state_keys": list(state_data.keys()),
        }

        logger.info(f"Session saved successfully: {session_file}")
        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error saving session state: {e}")
        return json.dumps({"status": "error", "error": str(e)})


async def load_session_state(
    session_name: str,
    tool_context: ToolContext,
) -> str:
    """Load session state from file.

    Args:
        session_name: Name of the session to load
        tool_context: Tool context to restore state into

    Returns:
        JSON string with load status
    """
    logger.info(f"Loading session state: {session_name}")

    try:
        session_file = Path("sessions") / f"{session_name}.json"

        if not session_file.exists():
            return json.dumps(
                {"status": "error", "error": f"Session file not found: {session_name}"}
            )

        # Load session data
        with open(session_file) as f:
            session_data = json.load(f)

        # Restore state
        if "state" in session_data:
            tool_context.state.update(session_data["state"])

        result = {
            "status": "success",
            "session_name": session_name,
            "loaded_timestamp": session_data.get("timestamp"),
            "restored_keys": list(session_data.get("state", {}).keys()),
        }

        logger.info(f"Session loaded successfully: {session_name}")
        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error loading session state: {e}")
        return json.dumps({"status": "error", "error": str(e)})
