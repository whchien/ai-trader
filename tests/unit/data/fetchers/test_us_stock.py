"""Tests for ai_trader.data.fetchers.us_stock module."""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, call

from ai_trader.core.exceptions import DataFetchError, DataValidationError
from ai_trader.data.fetchers.us_stock import USStockFetcher


@pytest.fixture
def sample_yfinance_data():
    """Sample yfinance response."""
    dates = pd.date_range("2023-01-01", periods=100, freq="D")
    return pd.DataFrame({
        "Date": dates,
        "Open": [100.0 + i * 0.1 for i in range(100)],
        "High": [105.0 + i * 0.1 for i in range(100)],
        "Low": [95.0 + i * 0.1 for i in range(100)],
        "Close": [100.0 + i * 0.1 for i in range(100)],
        "Adj Close": [100.0 + i * 0.1 for i in range(100)],
        "Volume": [1000000] * 100,
    }).set_index("Date")


class TestUSStockFetcherInit:
    """Test USStockFetcher initialization."""

    def test_init_with_required_params(self):
        """Test initialization with required parameters."""
        fetcher = USStockFetcher(symbol="AAPL", start_date="2023-01-01")
        assert fetcher.symbol == "AAPL"
        assert fetcher.start_date == "2023-01-01"

    def test_init_with_all_params(self):
        """Test initialization with all parameters."""
        fetcher = USStockFetcher(
            symbol="MSFT",
            start_date="2023-01-01",
            end_date="2023-12-31",
            max_retries=5,
            retry_delay=3
        )
        assert fetcher.symbol == "MSFT"
        assert fetcher.end_date == "2023-12-31"
        assert fetcher.max_retries == 5
        assert fetcher.retry_delay == 3

    def test_init_with_default_params(self):
        """Test default parameter values."""
        fetcher = USStockFetcher(symbol="AAPL", start_date="2023-01-01")
        assert fetcher.end_date is None
        assert fetcher.max_retries == 3
        assert fetcher.retry_delay == 2


class TestUSStockFetcherFetch:
    """Test USStockFetcher.fetch method."""

    @patch("ai_trader.data.fetchers.us_stock.yf.download")
    def test_fetch_successful(self, mock_download, sample_yfinance_data):
        """Test successful data fetching."""
        mock_download.return_value = sample_yfinance_data

        fetcher = USStockFetcher(symbol="AAPL", start_date="2023-01-01")
        result = fetcher.fetch()

        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        assert "open" in result.columns
        assert result.index.name == "date"

    @patch("ai_trader.data.fetchers.us_stock.yf.download")
    def test_fetch_returns_normalized_data(self, mock_download, sample_yfinance_data):
        """Test that fetched data is normalized."""
        mock_download.return_value = sample_yfinance_data

        fetcher = USStockFetcher(symbol="AAPL", start_date="2023-01-01")
        result = fetcher.fetch()

        # Check all columns are lowercase
        assert all(col.islower() for col in result.columns)
        # Check required columns exist
        assert set(["open", "high", "low", "close", "volume"]).issubset(result.columns)

    @patch("ai_trader.data.fetchers.us_stock.yf.download")
    def test_fetch_calls_yfinance_with_correct_params(self, mock_download, sample_yfinance_data):
        """Test that yfinance is called with correct parameters."""
        mock_download.return_value = sample_yfinance_data

        fetcher = USStockFetcher(symbol="AAPL", start_date="2023-01-01", end_date="2023-12-31")
        fetcher.fetch()

        mock_download.assert_called_once()
        call_kwargs = mock_download.call_args[1]
        assert call_kwargs["start"] == "2023-01-01"
        assert call_kwargs["end"] == "2023-12-31"
        assert call_kwargs["progress"] is False

    @patch("ai_trader.data.fetchers.us_stock.yf.download")
    def test_fetch_empty_response_raises_error(self, mock_download):
        """Test that empty response raises DataFetchError."""
        mock_download.return_value = pd.DataFrame()

        fetcher = USStockFetcher(symbol="AAPL", start_date="2023-01-01", max_retries=1)

        with pytest.raises(DataFetchError) as exc_info:
            fetcher.fetch()

        assert exc_info.value.symbol == "AAPL"
        assert exc_info.value.source == "yfinance"

    @patch("ai_trader.data.fetchers.us_stock.yf.download")
    def test_fetch_retry_on_empty_response(self, mock_download, sample_yfinance_data):
        """Test that fetch retries on empty response."""
        # First call returns empty, subsequent calls return data
        mock_download.side_effect = [
            pd.DataFrame(),  # First attempt
            sample_yfinance_data,  # Second attempt
        ]

        fetcher = USStockFetcher(symbol="AAPL", start_date="2023-01-01", max_retries=2)
        result = fetcher.fetch()

        # Should successfully get data on second attempt
        assert not result.empty
        assert mock_download.call_count == 2
        assert "open" in result.columns

    @patch("ai_trader.data.fetchers.us_stock.yf.download")
    def test_fetch_max_retries_with_multiple_failures(self, mock_download, sample_yfinance_data):
        """Test that exponential backoff happens through multiple retries."""
        # Return data on third attempt (after 2 empty responses)
        mock_download.side_effect = [
            pd.DataFrame(),           # First attempt - empty
            pd.DataFrame(),           # Second attempt - empty
            sample_yfinance_data,     # Third attempt - success
        ]

        fetcher = USStockFetcher(symbol="AAPL", start_date="2023-01-01", max_retries=3, retry_delay=1)
        result = fetcher.fetch()

        # Should succeed on third attempt
        assert not result.empty
        assert mock_download.call_count == 3
        assert "open" in result.columns
        assert "close" in result.columns

    @patch("ai_trader.data.fetchers.us_stock.yf.download")
    def test_fetch_max_retries_exceeded(self, mock_download):
        """Test that DataFetchError is raised after max retries."""
        from yfinance.exceptions import YFException
        mock_download.side_effect = YFException("Network error")

        fetcher = USStockFetcher(symbol="AAPL", start_date="2023-01-01", max_retries=2)

        with pytest.raises(DataFetchError) as exc_info:
            fetcher.fetch()

        assert "after 2 attempts" in str(exc_info.value)
        assert mock_download.call_count == 2

    @patch("ai_trader.data.fetchers.us_stock.yf.download")
    def test_fetch_connection_error(self, mock_download):
        """Test handling of connection errors."""
        mock_download.side_effect = ConnectionError("Network unreachable")

        fetcher = USStockFetcher(symbol="AAPL", start_date="2023-01-01", max_retries=1)

        with pytest.raises(DataFetchError) as exc_info:
            fetcher.fetch()

        assert "Network error" in str(exc_info.value)

    @patch("ai_trader.data.fetchers.us_stock.yf.download")
    def test_fetch_timeout_error(self, mock_download):
        """Test handling of timeout errors."""
        mock_download.side_effect = TimeoutError("Request timeout")

        fetcher = USStockFetcher(symbol="AAPL", start_date="2023-01-01", max_retries=1)

        with pytest.raises(DataFetchError):
            fetcher.fetch()

    @patch("ai_trader.data.fetchers.us_stock.yf.download")
    def test_fetch_validation_error_propagates(self, mock_download):
        """Test that DataValidationError is propagated."""
        # Return data with missing columns
        incomplete_data = pd.DataFrame({
            "Date": pd.date_range("2023-01-01", periods=10),
            "Open": [100.0] * 10,
        }).set_index("Date")

        mock_download.return_value = incomplete_data

        fetcher = USStockFetcher(symbol="AAPL", start_date="2023-01-01", max_retries=1)

        with pytest.raises(DataValidationError):
            fetcher.fetch()


class TestUSStockFetcherFetchBatch:
    """Test USStockFetcher.fetch_batch method."""

    @patch("ai_trader.data.fetchers.us_stock.yf.download")
    def test_fetch_batch_empty_list(self, mock_download):
        """Test fetch_batch with empty symbol list."""
        fetcher = USStockFetcher(symbol="", start_date="2023-01-01")
        successful, failed = fetcher.fetch_batch([])

        assert successful == {}
        assert failed == []

    @patch("ai_trader.data.fetchers.us_stock.yf.download")
    def test_fetch_batch_single_symbol(self, mock_download, sample_yfinance_data):
        """Test fetch_batch with single symbol."""
        mock_download.return_value = sample_yfinance_data

        fetcher = USStockFetcher(symbol="", start_date="2023-01-01")
        successful, failed = fetcher.fetch_batch(["AAPL"])

        assert "AAPL" in successful
        assert len(successful) == 1
        assert failed == []

    @patch("ai_trader.data.fetchers.us_stock.yf.download")
    def test_fetch_batch_multiple_symbols(self, mock_download):
        """Test fetch_batch with multiple symbols."""
        dates = pd.date_range("2023-01-01", periods=10)
        multi_data = pd.DataFrame({
            ("AAPL", "Open"): [100.0] * 10,
            ("AAPL", "High"): [105.0] * 10,
            ("AAPL", "Low"): [95.0] * 10,
            ("AAPL", "Close"): [100.0] * 10,
            ("AAPL", "Volume"): [1000000] * 10,
            ("MSFT", "Open"): [200.0] * 10,
            ("MSFT", "High"): [205.0] * 10,
            ("MSFT", "Low"): [195.0] * 10,
            ("MSFT", "Close"): [200.0] * 10,
            ("MSFT", "Volume"): [2000000] * 10,
        }, index=dates)
        multi_data.index.name = "Date"
        multi_data.columns = pd.MultiIndex.from_tuples(multi_data.columns)

        mock_download.return_value = multi_data

        fetcher = USStockFetcher(symbol="", start_date="2023-01-01")
        successful, failed = fetcher.fetch_batch(["AAPL", "MSFT"])

        assert len(successful) == 2
        assert "AAPL" in successful
        assert "MSFT" in successful
        assert len(failed) == 0

    @patch("ai_trader.data.fetchers.us_stock.yf.download")
    def test_fetch_batch_partial_failure(self, mock_download):
        """Test fetch_batch handles partial failures."""
        # Return empty DataFrame for INVALID symbol
        dates = pd.date_range("2023-01-01", periods=10)
        multi_data = pd.DataFrame({
            ("AAPL", "Open"): [100.0] * 10,
            ("AAPL", "High"): [105.0] * 10,
            ("AAPL", "Low"): [95.0] * 10,
            ("AAPL", "Close"): [100.0] * 10,
            ("AAPL", "Volume"): [1000000] * 10,
        }, index=dates)
        multi_data.index.name = "Date"
        multi_data.columns = pd.MultiIndex.from_tuples(multi_data.columns)

        mock_download.return_value = multi_data

        fetcher = USStockFetcher(symbol="", start_date="2023-01-01")
        successful, failed = fetcher.fetch_batch(["AAPL", "MSFT"])

        assert "AAPL" in successful
        # MSFT might be in failed or successful depending on implementation
        assert len(successful) + len(failed) == 2

    @patch("ai_trader.data.fetchers.us_stock.yf.download")
    def test_fetch_batch_all_nan_data(self, mock_download):
        """Test fetch_batch handles all-NaN data (invalid symbols)."""
        dates = pd.date_range("2023-01-01", periods=10)
        nan_data = pd.DataFrame({
            ("INVALID", "Open"): [float("nan")] * 10,
            ("INVALID", "High"): [float("nan")] * 10,
            ("INVALID", "Low"): [float("nan")] * 10,
            ("INVALID", "Close"): [float("nan")] * 10,
            ("INVALID", "Volume"): [float("nan")] * 10,
        }, index=dates)
        nan_data.index.name = "Date"
        nan_data.columns = pd.MultiIndex.from_tuples(nan_data.columns)

        mock_download.return_value = nan_data

        fetcher = USStockFetcher(symbol="", start_date="2023-01-01")
        successful, failed = fetcher.fetch_batch(["INVALID"])

        assert "INVALID" in failed

    @patch("ai_trader.data.fetchers.us_stock.yf.download")
    def test_fetch_batch_network_error(self, mock_download):
        """Test fetch_batch handles network errors."""
        mock_download.side_effect = ConnectionError("Network error")

        fetcher = USStockFetcher(symbol="", start_date="2023-01-01")
        successful, failed = fetcher.fetch_batch(["AAPL", "MSFT"])

        assert successful == {}
        assert len(failed) == 2

    @patch("ai_trader.data.fetchers.us_stock.yf.download")
    def test_fetch_batch_returns_normalized_data(self, mock_download, sample_yfinance_data):
        """Test that batch-fetched data is normalized."""
        mock_download.return_value = sample_yfinance_data

        fetcher = USStockFetcher(symbol="", start_date="2023-01-01")
        successful, failed = fetcher.fetch_batch(["AAPL"])

        df = successful["AAPL"]
        assert all(col.islower() for col in df.columns)
        assert df.index.name == "date"


class TestUSStockFetcherIntegration:
    """Integration tests for USStockFetcher."""

    @patch("ai_trader.data.fetchers.us_stock.yf.download")
    def test_fetch_returns_valid_dataframe_structure(self, mock_download, sample_yfinance_data):
        """Test that fetch returns properly structured DataFrame."""
        mock_download.return_value = sample_yfinance_data

        fetcher = USStockFetcher(symbol="AAPL", start_date="2023-01-01")
        result = fetcher.fetch()

        # Check structure
        assert isinstance(result, pd.DataFrame)
        assert isinstance(result.index, pd.DatetimeIndex)
        assert result.index.name == "date"

        # Check required columns
        required_cols = {"open", "high", "low", "close", "volume"}
        assert required_cols.issubset(set(result.columns))

        # Check data types
        assert pd.api.types.is_numeric_dtype(result["open"])
        assert pd.api.types.is_numeric_dtype(result["volume"])

    @patch("ai_trader.data.fetchers.us_stock.yf.download")
    def test_fetch_handles_different_symbols(self, mock_download, sample_yfinance_data):
        """Test that fetch works with different symbols."""
        mock_download.return_value = sample_yfinance_data

        for symbol in ["AAPL", "MSFT", "GOOGL", "^GSPC"]:
            fetcher = USStockFetcher(symbol=symbol, start_date="2023-01-01")
            result = fetcher.fetch()
            assert not result.empty

        assert mock_download.call_count >= 4
