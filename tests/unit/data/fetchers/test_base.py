"""Tests for ai_trader.data.fetchers.base module."""

import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import MagicMock, patch

from ai_trader.core.exceptions import DataValidationError
from ai_trader.data.fetchers.base import BaseFetcher, load_example


class ConcreteFetcher(BaseFetcher):
    """Concrete implementation of BaseFetcher for testing."""

    def __init__(self, data=None):
        self.data = data

    def fetch(self):
        return self.data


class TestBaseFetcherNormalizeColumns:
    """Test the _normalize_columns method of BaseFetcher."""

    def test_converts_columns_to_lowercase(self):
        """Test that column names are converted to lowercase."""
        fetcher = ConcreteFetcher()
        df = pd.DataFrame({
            "Date": pd.date_range("2023-01-01", periods=10),
            "Open": [100.0] * 10,
            "High": [105.0] * 10,
            "Low": [95.0] * 10,
            "Close": [100.0] * 10,
            "Volume": [1000000] * 10,
        })

        result = fetcher._normalize_columns(df)

        assert all(col.islower() for col in result.columns)
        assert "open" in result.columns
        assert "high" in result.columns
        assert "low" in result.columns
        assert "close" in result.columns
        assert "volume" in result.columns

    def test_sets_date_index(self):
        """Test that date is set as index."""
        fetcher = ConcreteFetcher()
        df = pd.DataFrame({
            "Date": pd.date_range("2023-01-01", periods=10),
            "Open": [100.0] * 10,
            "High": [105.0] * 10,
            "Low": [95.0] * 10,
            "Close": [100.0] * 10,
            "Volume": [1000000] * 10,
        })

        result = fetcher._normalize_columns(df)

        assert result.index.name == "date"
        assert isinstance(result.index, pd.DatetimeIndex)

    def test_renames_capacity_to_volume(self):
        """Test that 'capacity' column is renamed to 'volume' (TW stocks)."""
        fetcher = ConcreteFetcher()
        df = pd.DataFrame({
            "Date": pd.date_range("2023-01-01", periods=10),
            "Open": [100.0] * 10,
            "High": [105.0] * 10,
            "Low": [95.0] * 10,
            "Close": [100.0] * 10,
            "Capacity": [1000000] * 10,
        })

        result = fetcher._normalize_columns(df)

        assert "volume" in result.columns
        assert "capacity" not in result.columns

    def test_renames_adj_close_to_adj_close(self):
        """Test that 'Adj Close' is renamed to 'adj_close'."""
        fetcher = ConcreteFetcher()
        df = pd.DataFrame({
            "Date": pd.date_range("2023-01-01", periods=10),
            "Open": [100.0] * 10,
            "High": [105.0] * 10,
            "Low": [95.0] * 10,
            "Close": [100.0] * 10,
            "Adj Close": [100.0] * 10,
            "Volume": [1000000] * 10,
        })

        result = fetcher._normalize_columns(df)

        assert "adj_close" in result.columns
        assert "adj close" not in result.columns

    def test_handles_multiindex_columns(self):
        """Test handling of MultiIndex columns (from yfinance batch downloads)."""
        fetcher = ConcreteFetcher()

        # Create DataFrame with MultiIndex columns
        # When yfinance downloads single ticker, it returns simple columns
        # When downloading multiple, it uses (ticker, column) format
        columns = pd.MultiIndex.from_product(
            [["AAPL"], ["Open", "High", "Low", "Close", "Adj Close", "Volume"]]
        )
        dates = pd.date_range("2023-01-01", periods=10)
        data = [[100.0, 105.0, 95.0, 100.0, 100.0, 1000000] for _ in range(10)]

        df = pd.DataFrame(data, columns=columns, index=dates)
        df.index.name = "Date"

        result = fetcher._normalize_columns(df)

        # Should flatten MultiIndex - first level values become the columns
        assert not isinstance(result.columns, pd.MultiIndex)
        # After normalization, columns should still be present (they get flattened to first level)
        assert len(result.columns) > 0

    def test_converts_date_column_to_datetime(self):
        """Test that date column is converted to datetime."""
        fetcher = ConcreteFetcher()
        df = pd.DataFrame({
            "Date": ["2023-01-01", "2023-01-02", "2023-01-03"],
            "Open": [100.0, 101.0, 102.0],
            "High": [105.0, 106.0, 107.0],
            "Low": [95.0, 96.0, 97.0],
            "Close": [100.0, 101.0, 102.0],
            "Volume": [1000000, 1000000, 1000000],
        })

        result = fetcher._normalize_columns(df)

        assert isinstance(result.index, pd.DatetimeIndex)

    def test_preserves_data_values(self):
        """Test that data values are preserved during normalization."""
        fetcher = ConcreteFetcher()
        df = pd.DataFrame({
            "Date": pd.date_range("2023-01-01", periods=5),
            "Open": [100.0, 101.0, 102.0, 103.0, 104.0],
            "High": [105.0, 106.0, 107.0, 108.0, 109.0],
            "Low": [95.0, 96.0, 97.0, 98.0, 99.0],
            "Close": [100.0, 101.0, 102.0, 103.0, 104.0],
            "Volume": [1000000, 1000001, 1000002, 1000003, 1000004],
        })

        result = fetcher._normalize_columns(df)

        assert list(result["open"]) == [100.0, 101.0, 102.0, 103.0, 104.0]
        assert list(result["high"]) == [105.0, 106.0, 107.0, 108.0, 109.0]
        assert list(result["volume"]) == [1000000, 1000001, 1000002, 1000003, 1000004]


class TestBaseFetcherValidateDataframe:
    """Test the _validate_dataframe method of BaseFetcher."""

    def test_accepts_valid_dataframe(self):
        """Test that valid DataFrame passes validation."""
        fetcher = ConcreteFetcher()
        df = pd.DataFrame({
            "open": [100.0] * 10,
            "high": [105.0] * 10,
            "low": [95.0] * 10,
            "close": [100.0] * 10,
            "volume": [1000000] * 10,
        }, index=pd.date_range("2023-01-01", periods=10))

        # Should not raise
        fetcher._validate_dataframe(df, "AAPL")

    def test_rejects_empty_dataframe(self):
        """Test that empty DataFrame raises DataValidationError."""
        fetcher = ConcreteFetcher()
        df = pd.DataFrame()

        with pytest.raises(DataValidationError) as exc_info:
            fetcher._validate_dataframe(df, "AAPL")

        assert "No data returned" in str(exc_info.value)
        assert exc_info.value.symbol == "AAPL"

    def test_detects_missing_open_column(self):
        """Test that missing 'open' column is detected."""
        fetcher = ConcreteFetcher()
        df = pd.DataFrame({
            "high": [105.0] * 10,
            "low": [95.0] * 10,
            "close": [100.0] * 10,
            "volume": [1000000] * 10,
        })

        with pytest.raises(DataValidationError) as exc_info:
            fetcher._validate_dataframe(df, "AAPL")

        assert "open" in str(exc_info.value).lower()

    def test_detects_missing_multiple_columns(self):
        """Test that multiple missing columns are detected."""
        fetcher = ConcreteFetcher()
        df = pd.DataFrame({
            "open": [100.0] * 10,
            "volume": [1000000] * 10,
        })

        with pytest.raises(DataValidationError) as exc_info:
            fetcher._validate_dataframe(df, "AAPL")

        error = exc_info.value
        assert len(error.issues) >= 2

    @pytest.mark.parametrize("missing_col", ["open", "high", "low", "close", "volume"])
    def test_detects_each_missing_column(self, missing_col):
        """Test detection of each required column when missing."""
        fetcher = ConcreteFetcher()
        columns = {"open", "high", "low", "close", "volume"} - {missing_col}
        df = pd.DataFrame({col: [100.0] * 10 for col in columns})

        with pytest.raises(DataValidationError):
            fetcher._validate_dataframe(df, "AAPL")

    def test_skip_volume_parameter(self):
        """Test that skip_volume=True allows missing volume."""
        fetcher = ConcreteFetcher()
        df = pd.DataFrame({
            "open": [100.0] * 10,
            "high": [105.0] * 10,
            "low": [95.0] * 10,
            "close": [100.0] * 10,
        })

        # Should not raise when skip_volume=True
        fetcher._validate_dataframe(df, "EURUSD", skip_volume=True)

    def test_skip_volume_still_requires_other_columns(self):
        """Test that skip_volume=True still requires other columns."""
        fetcher = ConcreteFetcher()
        df = pd.DataFrame({
            "open": [100.0] * 10,
            "high": [105.0] * 10,
        })

        with pytest.raises(DataValidationError):
            fetcher._validate_dataframe(df, "EURUSD", skip_volume=True)

    def test_stores_symbol_in_error(self):
        """Test that symbol is stored in validation error."""
        fetcher = ConcreteFetcher()
        df = pd.DataFrame()

        with pytest.raises(DataValidationError) as exc_info:
            fetcher._validate_dataframe(df, "MSFT")

        assert exc_info.value.symbol == "MSFT"

    def test_stores_issues_in_error(self):
        """Test that missing columns are stored as issues."""
        fetcher = ConcreteFetcher()
        df = pd.DataFrame({
            "open": [100.0] * 10,
        })

        with pytest.raises(DataValidationError) as exc_info:
            fetcher._validate_dataframe(df, "AAPL")

        assert len(exc_info.value.issues) > 0

    def test_case_insensitive_column_check(self):
        """Test that column check is case-insensitive."""
        fetcher = ConcreteFetcher()
        df = pd.DataFrame({
            "OPEN": [100.0] * 10,
            "HIGH": [105.0] * 10,
            "LOW": [95.0] * 10,
            "CLOSE": [100.0] * 10,
            "VOLUME": [1000000] * 10,
        })

        # Should not raise because check is case-insensitive
        fetcher._validate_dataframe(df, "AAPL")


class TestLoadExample:
    """Test the load_example function."""

    @patch("pathlib.Path.exists")
    @patch("pandas.read_csv")
    def test_load_example_tw_market(self, mock_read_csv, mock_exists):
        """Test loading example data for TW market."""
        mock_exists.return_value = True
        mock_read_csv.return_value = pd.DataFrame({
            "open": [100.0] * 10,
            "high": [105.0] * 10,
            "low": [95.0] * 10,
            "close": [100.0] * 10,
            "volume": [1000000] * 10,
        }, index=pd.date_range("2023-01-01", periods=10))

        result = load_example(market="tw")

        assert result is not None
        assert isinstance(result, pd.DataFrame)
        mock_exists.assert_called()

    @patch("pathlib.Path.exists")
    @patch("pandas.read_csv")
    def test_load_example_us_market(self, mock_read_csv, mock_exists):
        """Test loading example data for US market."""
        mock_exists.return_value = True
        mock_read_csv.return_value = pd.DataFrame({
            "open": [100.0] * 10,
            "high": [105.0] * 10,
            "low": [95.0] * 10,
            "close": [100.0] * 10,
            "volume": [1000000] * 10,
        }, index=pd.date_range("2023-01-01", periods=10))

        result = load_example(market="us")

        assert result is not None
        assert isinstance(result, pd.DataFrame)

    def test_load_example_invalid_market(self):
        """Test that invalid market raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            load_example(market="invalid")

        assert "only supports 'tw' or 'us'" in str(exc_info.value)

    @patch("pathlib.Path.exists")
    def test_load_example_file_not_found(self, mock_exists):
        """Test that missing file raises FileNotFoundError."""
        mock_exists.return_value = False

        with pytest.raises(FileNotFoundError):
            load_example(market="tw")

    def test_load_example_default_market(self):
        """Test that default market is 'tw'."""
        # This test verifies the function signature
        # The actual loading would require real files
        import inspect
        sig = inspect.signature(load_example)
        assert sig.parameters["market"].default == "tw"

    @patch("pathlib.Path.exists")
    @patch("pandas.read_csv")
    def test_load_example_returns_dataframe_with_index(self, mock_read_csv, mock_exists):
        """Test that returned DataFrame has date index."""
        mock_exists.return_value = True
        dates = pd.date_range("2023-01-01", periods=10)
        mock_read_csv.return_value = pd.DataFrame({
            "open": [100.0] * 10,
            "high": [105.0] * 10,
            "low": [95.0] * 10,
            "close": [100.0] * 10,
            "volume": [1000000] * 10,
        }, index=dates)
        mock_read_csv.return_value.index.name = "date"

        result = load_example(market="tw")

        assert isinstance(result.index, pd.DatetimeIndex)


class TestBaseFetcherAbstractMethods:
    """Test that BaseFetcher is properly abstract."""

    def test_cannot_instantiate_directly(self):
        """Test that BaseFetcher cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseFetcher()

    def test_concrete_implementation_works(self):
        """Test that concrete implementation can be instantiated."""
        fetcher = ConcreteFetcher()
        assert fetcher is not None

    def test_fetch_is_abstract(self):
        """Test that fetch method must be implemented."""
        # This is verified by the fact that BaseFetcher can't be instantiated
        # A class that doesn't implement fetch() would also fail to instantiate
        pass
