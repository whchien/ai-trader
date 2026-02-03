"""Entry point for running the ai-trader MCP server."""

from ai_trader.mcp.server import mcp

if __name__ == "__main__":
    mcp.run(show_banner=False)
