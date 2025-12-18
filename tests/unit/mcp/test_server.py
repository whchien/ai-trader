"""Tests for ai_trader.mcp.server module."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio

# Try to import MCP modules, skip tests if dependencies are unavailable
mcp_available = True
try:
    from ai_trader.mcp import models, server
    from ai_trader.mcp.server import mcp
except (ImportError, ModuleNotFoundError) as e:
    mcp_available = False
    pytestmark = pytest.mark.skip(reason=f"MCP dependencies not available: {e}")


class TestMCPServerInitialization:
    """Test MCP server initialization."""

    def test_mcp_is_fastmcp_instance(self):
        """Test that mcp is a FastMCP instance."""
        from fastmcp import FastMCP
        assert isinstance(mcp, FastMCP)

    def test_mcp_has_name(self):
        """Test that MCP server has correct name."""
        assert mcp.name == "ai-trader"

    def test_mcp_has_tools(self):
        """Test that MCP server has registered tools."""
        # Check that tools are registered
        assert hasattr(mcp, 'tools') or hasattr(mcp, '_tools')


class TestRunBacktestTool:
    """Test the run_backtest tool."""

    @pytest.mark.asyncio
    async def test_run_backtest_with_valid_request(self):
        """Test running backtest with valid configuration."""
        request = models.RunBacktestRequest(
            config_file="/path/to/config.yaml",
            strategy=None,
            cash=100000,
            commission=0.001425
        )

        with patch("ai_trader.mcp.tools.backtest.run_backtest_tool") as mock_tool:
            mock_result = models.BacktestResult(
                strategy_name="SMAStrategy",
                initial_value=100000,
                final_value=110000,
                profit_loss=10000,
                return_pct=10.0,
                analyzers=models.AnalyzerResults(
                    sharpe_ratio=1.5,
                    total_return=10.0,
                    max_drawdown=-5.0,
                    total_trades=20,
                    won_trades=12,
                    lost_trades=8,
                    win_rate=60.0
                ),
                execution_time_seconds=2.5
            )
            mock_tool.return_value = mock_result

            result = await server.run_backtest(request, MagicMock())

            assert result.strategy_name == "SMAStrategy"
            assert result.initial_value == 100000
            assert result.final_value == 110000

    @pytest.mark.asyncio
    async def test_run_backtest_with_strategy_override(self):
        """Test backtest with strategy override."""
        request = models.RunBacktestRequest(
            config_file="/path/to/config.yaml",
            strategy="CustomStrategy",
            cash=500000,
            commission=0.001
        )

        with patch("ai_trader.mcp.tools.backtest.run_backtest_tool") as mock_tool:
            mock_result = models.BacktestResult(
                strategy_name="CustomStrategy",
                initial_value=500000,
                final_value=520000,
                profit_loss=20000,
                return_pct=4.0,
                analyzers=models.AnalyzerResults(),
                execution_time_seconds=3.0
            )
            mock_tool.return_value = mock_result

            result = await server.run_backtest(request, MagicMock())

            assert result.strategy_name == "CustomStrategy"
            assert result.initial_value == 500000

    @pytest.mark.asyncio
    async def test_run_backtest_with_none_overrides(self):
        """Test backtest where overrides are None."""
        request = models.RunBacktestRequest(
            config_file="/path/to/config.yaml"
        )

        with patch("ai_trader.mcp.tools.backtest.run_backtest_tool") as mock_tool:
            mock_result = models.BacktestResult(
                strategy_name="DefaultStrategy",
                initial_value=1000000,
                final_value=1050000,
                profit_loss=50000,
                return_pct=5.0,
                analyzers=models.AnalyzerResults(),
                execution_time_seconds=5.0
            )
            mock_tool.return_value = mock_result

            result = await server.run_backtest(request, MagicMock())

            assert result is not None
            assert result.return_pct == 5.0


class TestQuickBacktestTool:
    """Test the quick_backtest tool."""

    @pytest.mark.asyncio
    async def test_quick_backtest_with_required_fields(self):
        """Test quick backtest with only required fields."""
        request = models.QuickBacktestRequest(
            strategy_name="SMAStrategy",
            data_file="/path/to/data.csv"
        )

        with patch("ai_trader.mcp.tools.backtest.quick_backtest_tool") as mock_tool:
            mock_result = models.BacktestResult(
                strategy_name="SMAStrategy",
                initial_value=1000000,
                final_value=1050000,
                profit_loss=50000,
                return_pct=5.0,
                analyzers=models.AnalyzerResults(),
                execution_time_seconds=2.0
            )
            mock_tool.return_value = mock_result

            result = await server.quick_backtest(request, MagicMock())

            assert result.strategy_name == "SMAStrategy"
            assert result.initial_value == 1000000

    @pytest.mark.asyncio
    async def test_quick_backtest_with_custom_cash(self):
        """Test quick backtest with custom cash."""
        request = models.QuickBacktestRequest(
            strategy_name="SMAStrategy",
            data_file="/path/to/data.csv",
            cash=500000,
            commission=0.002
        )

        with patch("ai_trader.mcp.tools.backtest.quick_backtest_tool") as mock_tool:
            mock_result = models.BacktestResult(
                strategy_name="SMAStrategy",
                initial_value=500000,
                final_value=520000,
                profit_loss=20000,
                return_pct=4.0,
                analyzers=models.AnalyzerResults(),
                execution_time_seconds=2.0
            )
            mock_tool.return_value = mock_result

            result = await server.quick_backtest(request, MagicMock())

            assert result.initial_value == 500000

    @pytest.mark.asyncio
    async def test_quick_backtest_with_date_range(self):
        """Test quick backtest with date range."""
        request = models.QuickBacktestRequest(
            strategy_name="BBandsStrategy",
            data_file="/path/to/data.csv",
            start_date="2023-01-01",
            end_date="2023-12-31"
        )

        with patch("ai_trader.mcp.tools.backtest.quick_backtest_tool") as mock_tool:
            mock_result = models.BacktestResult(
                strategy_name="BBandsStrategy",
                initial_value=1000000,
                final_value=1100000,
                profit_loss=100000,
                return_pct=10.0,
                analyzers=models.AnalyzerResults(),
                execution_time_seconds=3.0
            )
            mock_tool.return_value = mock_result

            result = await server.quick_backtest(request, MagicMock())

            assert result.return_pct == 10.0


class TestFetchMarketDataTool:
    """Test the fetch_market_data tool."""

    @pytest.mark.asyncio
    async def test_fetch_single_us_stock(self):
        """Test fetching single US stock."""
        request = models.FetchDataRequest(
            symbols=["AAPL"],
            market="us_stock",
            start_date="2023-01-01"
        )

        with patch("ai_trader.mcp.tools.data.fetch_data_tool") as mock_tool:
            mock_result = models.FetchResult(
                successful_symbols=["AAPL"],
                failed_symbols=[],
                files_saved=[
                    models.FetchedSymbol(
                        symbol="AAPL",
                        filepath="/data/us_stock/AAPL_2023-01-01_to_2023-12-31.csv",
                        rows=252
                    )
                ],
                total_symbols=1,
                success_count=1
            )
            mock_tool.return_value = mock_result

            result = await server.fetch_market_data(request, MagicMock())

            assert result.success_count == 1
            assert "AAPL" in result.successful_symbols
            assert len(result.files_saved) == 1

    @pytest.mark.asyncio
    async def test_fetch_multiple_stocks(self):
        """Test fetching multiple stocks."""
        request = models.FetchDataRequest(
            symbols=["AAPL", "MSFT", "GOOGL"],
            market="us_stock",
            start_date="2023-01-01",
            end_date="2023-12-31"
        )

        with patch("ai_trader.mcp.tools.data.fetch_data_tool") as mock_tool:
            mock_result = models.FetchResult(
                successful_symbols=["AAPL", "MSFT", "GOOGL"],
                failed_symbols=[],
                files_saved=[
                    models.FetchedSymbol(symbol="AAPL", filepath="/data/us_stock/AAPL.csv", rows=252),
                    models.FetchedSymbol(symbol="MSFT", filepath="/data/us_stock/MSFT.csv", rows=252),
                    models.FetchedSymbol(symbol="GOOGL", filepath="/data/us_stock/GOOGL.csv", rows=252),
                ],
                total_symbols=3,
                success_count=3
            )
            mock_tool.return_value = mock_result

            result = await server.fetch_market_data(request, MagicMock())

            assert result.success_count == 3
            assert len(result.files_saved) == 3
            assert result.failed_symbols == []

    @pytest.mark.asyncio
    async def test_fetch_tw_stock(self):
        """Test fetching Taiwan stock."""
        request = models.FetchDataRequest(
            symbols=["2330"],
            market="tw_stock",
            start_date="2023-01-01"
        )

        with patch("ai_trader.mcp.tools.data.fetch_data_tool") as mock_tool:
            mock_result = models.FetchResult(
                successful_symbols=["2330"],
                failed_symbols=[],
                files_saved=[
                    models.FetchedSymbol(
                        symbol="2330",
                        filepath="/data/tw_stock/2330_2023-01-01_to_2023-12-31.csv",
                        rows=245
                    )
                ],
                total_symbols=1,
                success_count=1
            )
            mock_tool.return_value = mock_result

            result = await server.fetch_market_data(request, MagicMock())

            assert result.success_count == 1

    @pytest.mark.asyncio
    async def test_fetch_cryptocurrency(self):
        """Test fetching cryptocurrency data."""
        request = models.FetchDataRequest(
            symbols=["BTC-USD", "ETH-USD"],
            market="crypto",
            start_date="2023-01-01"
        )

        with patch("ai_trader.mcp.tools.data.fetch_data_tool") as mock_tool:
            mock_result = models.FetchResult(
                successful_symbols=["BTC-USD", "ETH-USD"],
                failed_symbols=[],
                files_saved=[
                    models.FetchedSymbol(symbol="BTC-USD", filepath="/data/crypto/BTC-USD.csv", rows=365),
                    models.FetchedSymbol(symbol="ETH-USD", filepath="/data/crypto/ETH-USD.csv", rows=365),
                ],
                total_symbols=2,
                success_count=2
            )
            mock_tool.return_value = mock_result

            result = await server.fetch_market_data(request, MagicMock())

            assert result.success_count == 2

    @pytest.mark.asyncio
    async def test_fetch_with_partial_failure(self):
        """Test fetch with some symbols failing."""
        request = models.FetchDataRequest(
            symbols=["AAPL", "INVALID"],
            market="us_stock",
            start_date="2023-01-01"
        )

        with patch("ai_trader.mcp.tools.data.fetch_data_tool") as mock_tool:
            mock_result = models.FetchResult(
                successful_symbols=["AAPL"],
                failed_symbols=["INVALID"],
                files_saved=[
                    models.FetchedSymbol(symbol="AAPL", filepath="/data/us_stock/AAPL.csv", rows=252),
                ],
                total_symbols=2,
                success_count=1
            )
            mock_tool.return_value = mock_result

            result = await server.fetch_market_data(request, MagicMock())

            assert result.success_count == 1
            assert "INVALID" in result.failed_symbols

    @pytest.mark.asyncio
    async def test_fetch_with_custom_output_dir(self):
        """Test fetch with custom output directory."""
        request = models.FetchDataRequest(
            symbols=["AAPL"],
            market="us_stock",
            start_date="2023-01-01",
            output_dir="/custom/data/dir"
        )

        with patch("ai_trader.mcp.tools.data.fetch_data_tool") as mock_tool:
            mock_result = models.FetchResult(
                successful_symbols=["AAPL"],
                failed_symbols=[],
                files_saved=[
                    models.FetchedSymbol(
                        symbol="AAPL",
                        filepath="/custom/data/dir/us_stock/AAPL.csv",
                        rows=252
                    )
                ],
                total_symbols=1,
                success_count=1
            )
            mock_tool.return_value = mock_result

            result = await server.fetch_market_data(request, MagicMock())

            assert "/custom/data/dir" in result.files_saved[0].filepath


class TestListStrategiesTool:
    """Test the list_strategies tool."""

    @pytest.mark.asyncio
    async def test_list_all_strategies(self):
        """Test listing all strategies."""
        request = models.ListStrategiesRequest(strategy_type="all")

        with patch("ai_trader.mcp.tools.strategies.list_strategies_tool") as mock_tool:
            mock_result = models.StrategiesResult(
                classic_strategies=[
                    models.StrategyInfo(
                        name="SMAStrategy",
                        description="Simple Moving Average strategy",
                        type="classic"
                    ),
                    models.StrategyInfo(
                        name="BBandsStrategy",
                        description="Bollinger Bands strategy",
                        type="classic"
                    ),
                ],
                portfolio_strategies=[
                    models.StrategyInfo(
                        name="TripleRSIRotation",
                        description="Portfolio rotation based on RSI",
                        type="portfolio"
                    ),
                ]
            )
            mock_tool.return_value = mock_result

            result = await server.list_strategies(request)

            assert len(result.classic_strategies) == 2
            assert len(result.portfolio_strategies) == 1

    @pytest.mark.asyncio
    async def test_list_classic_strategies_only(self):
        """Test listing only classic strategies."""
        request = models.ListStrategiesRequest(strategy_type="classic")

        with patch("ai_trader.mcp.tools.strategies.list_strategies_tool") as mock_tool:
            mock_result = models.StrategiesResult(
                classic_strategies=[
                    models.StrategyInfo(
                        name="SMAStrategy",
                        description="Simple Moving Average strategy",
                        type="classic"
                    ),
                ],
                portfolio_strategies=[]
            )
            mock_tool.return_value = mock_result

            result = await server.list_strategies(request)

            assert len(result.classic_strategies) > 0

    @pytest.mark.asyncio
    async def test_list_portfolio_strategies_only(self):
        """Test listing only portfolio strategies."""
        request = models.ListStrategiesRequest(strategy_type="portfolio")

        with patch("ai_trader.mcp.tools.strategies.list_strategies_tool") as mock_tool:
            mock_result = models.StrategiesResult(
                classic_strategies=[],
                portfolio_strategies=[
                    models.StrategyInfo(
                        name="TripleRSIRotation",
                        description="Portfolio rotation based on RSI",
                        type="portfolio"
                    ),
                ]
            )
            mock_tool.return_value = mock_result

            result = await server.list_strategies(request)

            assert len(result.portfolio_strategies) > 0


class TestMCPModels:
    """Test Pydantic models for request/response validation."""

    def test_run_backtest_request_validation(self):
        """Test RunBacktestRequest model validation."""
        request = models.RunBacktestRequest(
            config_file="/path/to/config.yaml",
            strategy="SMAStrategy",
            cash=500000,
            commission=0.002
        )

        assert request.config_file == "/path/to/config.yaml"
        assert request.strategy == "SMAStrategy"
        assert request.cash == 500000
        assert request.commission == 0.002

    def test_quick_backtest_request_defaults(self):
        """Test QuickBacktestRequest default values."""
        request = models.QuickBacktestRequest(
            strategy_name="SMAStrategy",
            data_file="/path/to/data.csv"
        )

        assert request.cash == 1000000
        assert request.commission == 0.001425

    def test_fetch_data_request_validation(self):
        """Test FetchDataRequest model validation."""
        request = models.FetchDataRequest(
            symbols=["AAPL", "MSFT"],
            market="us_stock",
            start_date="2023-01-01",
            end_date="2023-12-31"
        )

        assert len(request.symbols) == 2
        assert request.market == "us_stock"

    def test_backtest_result_model(self):
        """Test BacktestResult model structure."""
        result = models.BacktestResult(
            strategy_name="SMAStrategy",
            initial_value=100000,
            final_value=110000,
            profit_loss=10000,
            return_pct=10.0,
            analyzers=models.AnalyzerResults(sharpe_ratio=1.5),
            execution_time_seconds=2.5
        )

        assert result.profit_loss == 10000
        assert result.return_pct == 10.0

    def test_fetch_result_model(self):
        """Test FetchResult model structure."""
        result = models.FetchResult(
            successful_symbols=["AAPL"],
            failed_symbols=[],
            files_saved=[
                models.FetchedSymbol(
                    symbol="AAPL",
                    filepath="/data/AAPL.csv",
                    rows=252
                )
            ],
            total_symbols=1,
            success_count=1
        )

        assert result.success_count == 1
        assert len(result.files_saved) == 1

    def test_strategies_result_model(self):
        """Test StrategiesResult model structure."""
        result = models.StrategiesResult(
            classic_strategies=[
                models.StrategyInfo(
                    name="SMAStrategy",
                    description="Simple Moving Average strategy",
                    type="classic"
                )
            ],
            portfolio_strategies=[]
        )

        assert len(result.classic_strategies) == 1


class TestMCPRequestValidation:
    """Test request validation and error handling."""

    def test_fetch_data_request_invalid_market(self):
        """Test FetchDataRequest rejects invalid market."""
        with pytest.raises(ValueError):
            models.FetchDataRequest(
                symbols=["AAPL"],
                market="invalid_market",  # type: ignore
                start_date="2023-01-01"
            )

    def test_list_strategies_request_invalid_type(self):
        """Test ListStrategiesRequest rejects invalid type."""
        with pytest.raises(ValueError):
            models.ListStrategiesRequest(
                strategy_type="invalid_type"  # type: ignore
            )

    def test_strategy_info_invalid_type(self):
        """Test StrategyInfo rejects invalid type."""
        with pytest.raises(ValueError):
            models.StrategyInfo(
                name="TestStrategy",
                description="Test",
                type="invalid"  # type: ignore
            )
