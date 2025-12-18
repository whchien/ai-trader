"""Model Context Protocol server for ai-trader.

This module provides an MCP server that exposes ai-trader functionality
through the Model Context Protocol, enabling LLMs to interact with the
backtesting framework.

Example:
    Run the server locally:

    >>> from ai_trader.mcp.server import mcp
    >>> mcp.run()

    Or using the command line:

    >>> python -m ai_trader.mcp
"""

from ai_trader.mcp.server import mcp

__all__ = ["mcp"]
__version__ = "0.1.0"
