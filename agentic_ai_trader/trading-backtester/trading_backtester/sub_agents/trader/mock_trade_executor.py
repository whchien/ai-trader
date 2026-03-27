"""Mock trade execution tool for simulated trading."""

import json
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)


async def mock_execute_trade(
    symbol: str,
    action: str,
    quantity: int,
    order_type: str = "MARKET",
    limit_price: Optional[float] = None,
    fill_price: Optional[float] = None,
    tool_context: ToolContext = None,
) -> str:
    """Execute a mock (simulated) trade order.

    IMPORTANT: This is a simulated trading environment. No real trades are executed.

    Args:
        symbol: Stock symbol (e.g., 'AAPL', 'BTC')
        action: 'BUY' or 'SELL'
        quantity: Number of shares/units to trade
        order_type: 'MARKET' (default) or 'LIMIT'
        limit_price: Price for LIMIT orders (ignored for MARKET orders)
        fill_price: Actual fill price (defaults to limit_price for LIMIT, random for MARKET)
        tool_context: Tool context for state management

    Returns:
        JSON string with mock order details including order_id, status, and warning
    """
    logger.info(f"Executing mock trade: {action} {quantity} {symbol} @ {order_type}")

    try:
        # Validate inputs
        if action.upper() not in ("BUY", "SELL"):
            return json.dumps({
                "error": "Invalid action. Must be 'BUY' or 'SELL'",
                "action": action,
            })

        if order_type.upper() not in ("MARKET", "LIMIT"):
            return json.dumps({
                "error": "Invalid order_type. Must be 'MARKET' or 'LIMIT'",
                "order_type": order_type,
            })

        if quantity <= 0:
            return json.dumps({
                "error": "Quantity must be positive",
                "quantity": quantity,
            })

        # Generate mock order ID
        order_id = f"MOCK-{uuid4().hex[:8].upper()}"
        timestamp = datetime.now(timezone.utc).isoformat()

        # Determine status and fill price
        status = "FILLED" if order_type.upper() == "MARKET" else "PENDING"

        # For MARKET orders, use provided fill_price or estimate
        if order_type.upper() == "MARKET":
            if fill_price is None:
                # Simulate realistic market fill with small slippage
                fill_price = limit_price or 100.0
            actual_fill_price = fill_price
        else:
            # LIMIT orders pending at limit price
            actual_fill_price = limit_price or fill_price or 0.0

        # Create order record
        order = {
            "order_id": order_id,
            "status": status,
            "symbol": symbol.upper(),
            "action": action.upper(),
            "quantity": quantity,
            "order_type": order_type.upper(),
            "limit_price": limit_price,
            "fill_price": actual_fill_price,
            "timestamp": timestamp,
            "warning": "THIS IS A SIMULATED ORDER. No real trade was placed. This is for testing and learning purposes only.",
        }

        # Append to mock_trade_orders in context if available
        if tool_context:
            if "mock_trade_orders" not in tool_context.state:
                tool_context.state["mock_trade_orders"] = []
            tool_context.state["mock_trade_orders"].append(order)
            logger.info(f"Mock order recorded: {order_id} - {status}")

        logger.info(f"Mock trade executed: {order_id}")
        return json.dumps(order, indent=2)

    except Exception as e:
        error_msg = f"Mock trade execution failed: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})
