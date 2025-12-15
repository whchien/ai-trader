"""Main entry point for the trading backtester."""

import logging
import sys
from pathlib import Path

# Add the parent directory to the path to import ai_trader
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from trading_backtester.agent import root_agent
from trading_backtester.core.config import config

logger = logging.getLogger(__name__)


def main():
    """Main function to run the trading backtester."""
    try:
        # Validate configuration
        config.validate()

        logger.info("Trading Backtester initialized successfully")
        logger.info(f"Using model: {config.get_model('root_agent')}")
        logger.info(f"Default cash: ${config.get('backtesting.default_cash'):,}")

        # The agent is ready to be used by ADK
        print("Trading Backtester Agent is ready!")
        print("Use 'adk run trading_backtester' or 'adk web' to interact with the agent.")

        return root_agent

    except Exception as e:
        logger.error(f"Failed to initialize Trading Backtester: {e}")
        raise


if __name__ == "__main__":
    main()
