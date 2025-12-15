"""Tests for the Root Coordinator Agent."""

from unittest.mock import Mock, patch

import pytest
from trading_backtester.tools.coordinator_tools import (
    get_available_strategies,
    get_market_data_summary,
)


class TestCoordinatorTools:
    """Test suite for coordinator tools."""

    @pytest.mark.asyncio
    async def test_get_available_strategies(self):
        """Test getting available strategies."""
        # Mock tool context
        mock_context = Mock()
        mock_context.state = {}

        # Test getting all strategies
        result = await get_available_strategies(tool_context=mock_context)

        # Should return JSON string
        assert isinstance(result, str)
        assert "total_strategies" in result

        # Test filtering by type
        result_classic = await get_available_strategies(
            strategy_type="classic", tool_context=mock_context
        )
        assert isinstance(result_classic, str)
        assert "classic" in result_classic

    @pytest.mark.asyncio
    async def test_get_market_data_summary_mock(self):
        """Test market data summary with mocked data."""
        mock_context = Mock()
        mock_context.state = {}

        # Mock the MarketDataFetcher
        with patch(
            "trading_backtester.tools.coordinator_tools.MarketDataFetcher"
        ) as mock_fetcher_class:
            # Create mock data
            import numpy as np
            import pandas as pd

            dates = pd.date_range("2023-01-01", periods=100, freq="D")
            mock_df = pd.DataFrame(
                {
                    "Open": np.random.randn(100).cumsum() + 100,
                    "High": np.random.randn(100).cumsum() + 105,
                    "Low": np.random.randn(100).cumsum() + 95,
                    "Close": np.random.randn(100).cumsum() + 100,
                    "Volume": np.random.randint(1000000, 10000000, 100),
                },
                index=dates,
            )

            # Configure mock
            mock_fetcher = Mock()
            mock_fetcher.fetch_data.return_value = mock_df
            mock_fetcher_class.return_value = mock_fetcher

            # Test the function
            result = await get_market_data_summary(
                symbol="AAPL", period="1y", tool_context=mock_context
            )

            # Verify result
            assert isinstance(result, str)
            assert "AAPL" in result
            assert "price_info" in result

    def test_config_loading(self):
        """Test configuration loading."""
        from trading_backtester.core.config import config

        # Test basic config access
        assert config.get("backtesting.default_cash") is not None
        assert config.get("backtesting.default_commission") is not None

        # Test model configuration
        root_model = config.get_model("root_agent")
        assert root_model is not None
        assert isinstance(root_model, str)

    def test_utils_functions(self):
        """Test utility functions."""
        from trading_backtester.core.utils import (
            format_performance_summary,
            generate_parameter_grid,
            validate_date_range,
        )

        # Test date validation
        start, end = validate_date_range("2023-01-01", "2023-12-31")
        assert start == "2023-01-01"
        assert end == "2023-12-31"

        # Test parameter grid generation
        param_ranges = {"period": [10, 20, 30], "threshold": [0.1, 0.2]}
        grid = generate_parameter_grid(param_ranges)
        assert len(grid) == 6  # 3 * 2 combinations

        # Test performance summary formatting
        metrics = {
            "total_return": 15.5,
            "sharpe_ratio": 1.2,
            "max_drawdown": -8.3,
            "win_rate": 65.0,
        }
        summary = format_performance_summary(metrics)
        assert "15.50%" in summary
        assert "1.20" in summary


if __name__ == "__main__":
    pytest.main([__file__])
