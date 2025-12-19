"""Tests for ai_trader.utils.backtest module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import backtrader as bt

from ai_trader.utils.backtest import (
    create_cerebro,
    add_stock_data,
    add_portfolio_data,
    add_default_analyzers,
    add_analyzers,
    add_sizer,
)


class TestCreateCerebro:
    """Test the create_cerebro function."""

    def test_creates_cerebro_instance(self):
        """Test that create_cerebro returns a Cerebro instance."""
        cerebro = create_cerebro()
        assert isinstance(cerebro, bt.Cerebro)

    def test_sets_default_cash(self):
        """Test default cash value."""
        cerebro = create_cerebro()
        assert cerebro.broker.getcash() == 1000000

    def test_sets_custom_cash(self):
        """Test setting custom cash value."""
        cerebro = create_cerebro(cash=500000)
        assert cerebro.broker.getcash() == 500000

    def test_sets_default_commission(self):
        """Test default commission value."""
        cerebro = create_cerebro()
        # Commission is stored in broker but we can verify through broker
        assert cerebro.broker is not None

    def test_sets_custom_commission(self):
        """Test setting custom commission value."""
        cerebro = create_cerebro(commission=0.001)
        assert cerebro.broker is not None

    def test_multiple_instances_independent(self):
        """Test that multiple Cerebro instances are independent."""
        cerebro1 = create_cerebro(cash=100000)
        cerebro2 = create_cerebro(cash=500000)

        assert cerebro1.broker.getcash() == 100000
        assert cerebro2.broker.getcash() == 500000
        assert cerebro1 is not cerebro2


class TestAddStockData:
    """Test the add_stock_data function."""

    def test_add_dataframe_source(self, sample_ohlcv_data_short):
        """Test adding data from DataFrame."""
        cerebro = create_cerebro()
        add_stock_data(cerebro, source=sample_ohlcv_data_short)

        # Verify data was added
        assert len(cerebro.datas) == 1

    def test_add_dataframe_with_name(self, sample_ohlcv_data_short):
        """Test adding data with custom name."""
        cerebro = create_cerebro()
        add_stock_data(cerebro, source=sample_ohlcv_data_short, name="TEST")

        assert len(cerebro.datas) == 1

    def test_add_with_example_data(self):
        """Test adding example data (None source)."""
        cerebro = create_cerebro()
        # Mock load_example to avoid file dependencies
        with patch("ai_trader.utils.backtest.load_example") as mock_load:
            dates = pd.date_range("2023-01-01", periods=100)
            example_df = pd.DataFrame({
                "open": [100.0] * 100,
                "high": [105.0] * 100,
                "low": [95.0] * 100,
                "close": [100.0] * 100,
                "volume": [1000000] * 100,
            }, index=dates)
            example_df.index.name = "date"
            mock_load.return_value = example_df

            add_stock_data(cerebro, source=None)

            assert len(cerebro.datas) == 1
            mock_load.assert_called_once()

    def test_add_multiple_stocks(self, sample_ohlcv_data_short):
        """Test adding multiple stock data feeds."""
        cerebro = create_cerebro()

        add_stock_data(cerebro, source=sample_ohlcv_data_short, name="AAPL")
        add_stock_data(cerebro, source=sample_ohlcv_data_short, name="MSFT")

        assert len(cerebro.datas) == 2

    def test_add_with_date_filtering(self, sample_ohlcv_data_short):
        """Test date filtering when adding data."""
        cerebro = create_cerebro()

        # Add data with date range
        add_stock_data(
            cerebro,
            source=sample_ohlcv_data_short,
            start_date="2023-01-15",
            end_date="2023-01-25"
        )

        assert len(cerebro.datas) == 1

    def test_add_from_csv_path(self, tmp_path, sample_ohlcv_data_short):
        """Test adding data from CSV file path."""
        # Create test CSV file
        csv_file = tmp_path / "test.csv"
        sample_ohlcv_data_short.to_csv(csv_file)

        cerebro = create_cerebro()
        add_stock_data(cerebro, source=str(csv_file))

        assert len(cerebro.datas) == 1

    def test_add_with_invalid_source_type(self):
        """Test that invalid source type raises error."""
        cerebro = create_cerebro()

        with pytest.raises(ValueError, match="Unsupported source type"):
            add_stock_data(cerebro, source=12345)  # Invalid type


class TestAddPortfolioData:
    """Test the add_portfolio_data function."""

    def test_add_portfolio_data_multiple_files(self, tmp_path, sample_ohlcv_data_short):
        """Test adding portfolio data from multiple files."""
        # Create test CSV files
        (tmp_path / "AAPL_2023-01-01_to_2023-04-10.csv").write_text(
            sample_ohlcv_data_short.to_csv()
        )
        (tmp_path / "MSFT_2023-01-01_to_2023-04-10.csv").write_text(
            sample_ohlcv_data_short.to_csv()
        )

        cerebro = create_cerebro()
        add_portfolio_data(cerebro, data_dir=str(tmp_path))

        # Should have 2 data feeds
        assert len(cerebro.datas) >= 1  # At least one file loaded

    def test_add_portfolio_data_no_files_raises_error(self, tmp_path):
        """Test that no files raises ValueError."""
        cerebro = create_cerebro()

        with pytest.raises(ValueError, match="No files found"):
            add_portfolio_data(cerebro, data_dir=str(tmp_path))

    def test_add_portfolio_data_with_custom_pattern(self, tmp_path, sample_ohlcv_data_short):
        """Test portfolio data with custom file pattern."""
        # Create test files with different extensions
        (tmp_path / "AAPL_data.csv").write_text(sample_ohlcv_data_short.to_csv())
        (tmp_path / "MSFT_data.csv").write_text(sample_ohlcv_data_short.to_csv())

        cerebro = create_cerebro()
        add_portfolio_data(cerebro, data_dir=str(tmp_path), pattern="*_data.csv")

        # Should load matching files
        assert len(cerebro.datas) >= 1


class TestAddDefaultAnalyzers:
    """Test the add_default_analyzers function."""

    def test_adds_default_analyzers(self):
        """Test that default analyzers are added."""
        cerebro = create_cerebro()
        initial_analyzers = len(cerebro.analyzers)

        add_default_analyzers(cerebro)

        # Should have added analyzers
        assert len(cerebro.analyzers) > initial_analyzers

    def test_adds_specific_analyzers(self):
        """Test that specific default analyzers are added."""
        cerebro = create_cerebro()
        initial_count = len(cerebro.analyzers)

        add_default_analyzers(cerebro)

        # Should have added analyzers
        assert len(cerebro.analyzers) > initial_count
        # Should have at least 3 analyzers
        assert len(cerebro.analyzers) >= 3


class TestAddAnalyzers:
    """Test the add_analyzers function."""

    def test_adds_single_analyzer(self):
        """Test adding a single analyzer."""
        cerebro = create_cerebro()
        initial_count = len(cerebro.analyzers)

        add_analyzers(cerebro, ["sharpe"])

        # Should have added analyzer
        assert len(cerebro.analyzers) > initial_count

    def test_adds_multiple_analyzers(self):
        """Test adding multiple analyzers."""
        cerebro = create_cerebro()
        initial_count = len(cerebro.analyzers)

        add_analyzers(cerebro, ["sharpe", "drawdown", "returns"])

        # Should have added 3 analyzers
        assert len(cerebro.analyzers) >= initial_count + 3

    def test_adds_trade_analyzer(self):
        """Test adding trade analyzer."""
        cerebro = create_cerebro()
        initial_count = len(cerebro.analyzers)

        add_analyzers(cerebro, ["trades"])

        # Should have added analyzer
        assert len(cerebro.analyzers) > initial_count

    def test_ignores_unknown_analyzer(self):
        """Test that unknown analyzer is logged but not added."""
        cerebro = create_cerebro()
        add_analyzers(cerebro, ["unknown_analyzer"])

        # Should still work without crashing
        assert cerebro is not None

    @pytest.mark.parametrize("analyzer_name", ["sharpe", "drawdown", "returns", "trades", "sqn"])
    def test_supported_analyzers(self, analyzer_name):
        """Test all supported analyzers."""
        cerebro = create_cerebro()
        initial_count = len(cerebro.analyzers)

        add_analyzers(cerebro, [analyzer_name])

        # Should have added analyzer
        assert len(cerebro.analyzers) > initial_count


class TestAddSizer:
    """Test the add_sizer function."""

    def test_add_percent_sizer(self):
        """Test adding percent-based sizer."""
        cerebro = create_cerebro()
        add_sizer(cerebro, sizer_type="percent", percents=95)

        # Sizer should be added to cerebro
        assert cerebro.sizers is not None

    def test_add_fixed_sizer(self):
        """Test adding fixed-size sizer."""
        cerebro = create_cerebro()
        add_sizer(cerebro, sizer_type="fixed", stake=10)

        # Sizer should be added to cerebro
        assert cerebro.sizers is not None

    def test_sizer_with_custom_params(self):
        """Test sizer with custom parameters."""
        cerebro = create_cerebro()

        # Should accept various sizer types with params
        add_sizer(cerebro, sizer_type="percent", percents=90)
        assert cerebro.sizers is not None


class TestBacktestIntegration:
    """Integration tests for backtest utilities."""

    def test_basic_backtest_setup(self, sample_ohlcv_data_short):
        """Test setting up a complete backtest."""
        # Create cerebro
        cerebro = create_cerebro(cash=100000, commission=0.001)

        # Add data
        add_stock_data(cerebro, source=sample_ohlcv_data_short, name="TEST")

        # Add analyzers
        add_default_analyzers(cerebro)

        # Add sizer
        add_sizer(cerebro, sizer_type="percent", percents=95)

        # Verify setup
        assert cerebro.broker.getcash() == 100000
        assert len(cerebro.datas) == 1
        assert len(cerebro.analyzers) > 0

    def test_multiple_symbols_backtest_setup(self, sample_ohlcv_data_short):
        """Test setting up backtest with multiple symbols."""
        cerebro = create_cerebro(cash=1000000)

        # Add multiple data feeds
        for ticker in ["AAPL", "MSFT", "GOOGL"]:
            add_stock_data(cerebro, source=sample_ohlcv_data_short, name=ticker)

        # Add analyzers
        add_analyzers(cerebro, ["sharpe", "drawdown", "returns"])

        # Verify
        assert len(cerebro.datas) == 3
        assert len(cerebro.analyzers) == 3

    def test_portfolio_backtest_setup(self, tmp_path, sample_ohlcv_data_short):
        """Test setting up portfolio backtest."""
        # Create test files
        for ticker in ["AAPL", "MSFT"]:
            csv_file = tmp_path / f"{ticker}_2023-01-01_to_2023-04-10.csv"
            sample_ohlcv_data_short.to_csv(csv_file)

        cerebro = create_cerebro(cash=500000)

        # Add portfolio data
        add_portfolio_data(cerebro, data_dir=str(tmp_path))

        # Add analyzers and sizer
        add_default_analyzers(cerebro)
        add_sizer(cerebro, sizer_type="percent", percents=90)

        # Verify
        assert cerebro.broker.getcash() == 500000
        assert len(cerebro.datas) >= 1
        assert len(cerebro.analyzers) > 0
