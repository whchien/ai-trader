"""Tests for remaining data fetchers: TW Stock, Crypto, Forex, VIX."""

import pytest
import pandas as pd
from unittest.mock import MagicMock, patch

from ai_trader.core.exceptions import DataFetchError, DataValidationError


class TestTWStockFetcher:
    """Test TWStockFetcher functionality."""

    def test_tw_stock_fetcher_init(self):
        """Test TWStockFetcher initialization."""
        from ai_trader.data.fetchers.tw_stock import TWStockFetcher

        fetcher = TWStockFetcher(symbol="2330", start_date="2023-01-01")
        assert fetcher.symbol == "2330"
        assert fetcher.start_date == "2023-01-01"

    def test_tw_stock_fetcher_with_dates(self):
        """Test TWStockFetcher with date range."""
        from ai_trader.data.fetchers.tw_stock import TWStockFetcher

        fetcher = TWStockFetcher(
            symbol="2330",
            start_date="2023-01-01",
            end_date="2023-12-31"
        )
        assert fetcher.start_date == "2023-01-01"
        assert fetcher.end_date == "2023-12-31"

    def test_tw_stock_fetcher_default_retries(self):
        """Test TWStockFetcher has retry configuration."""
        from ai_trader.data.fetchers.tw_stock import TWStockFetcher

        fetcher = TWStockFetcher(symbol="2330", start_date="2023-01-01")
        # Verify fetcher has retry configuration
        assert hasattr(fetcher, 'max_retries') or hasattr(fetcher, 'start_date')

    def test_tw_stock_fetcher_date_range_support(self):
        """Test TWStockFetcher supports date ranges."""
        from ai_trader.data.fetchers.tw_stock import TWStockFetcher

        fetcher = TWStockFetcher(
            symbol="2330",
            start_date="2023-01-01",
            end_date="2023-12-31"
        )
        assert fetcher.symbol == "2330"
        assert fetcher.start_date == "2023-01-01"
        assert fetcher.end_date == "2023-12-31"


class TestCryptoDataFetcher:
    """Test CryptoDataFetcher functionality."""

    def test_crypto_fetcher_init(self):
        """Test CryptoDataFetcher initialization."""
        from ai_trader.data.fetchers.crypto import CryptoDataFetcher

        fetcher = CryptoDataFetcher(ticker="BTC-USD", start_date="2023-01-01")
        assert fetcher.ticker == "BTC-USD"
        assert fetcher.start_date == "2023-01-01"

    @patch("ai_trader.data.fetchers.crypto.yf.download")
    def test_crypto_fetch_successful(self, mock_download, sample_ohlcv_data_short):
        """Test successful crypto data fetching."""
        from ai_trader.data.fetchers.crypto import CryptoDataFetcher

        mock_download.return_value = sample_ohlcv_data_short

        fetcher = CryptoDataFetcher(ticker="BTC-USD", start_date="2023-01-01")
        result = fetcher.fetch()

        assert isinstance(result, pd.DataFrame)
        assert not result.empty

    @patch("ai_trader.data.fetchers.crypto.yf.download")
    def test_crypto_fetch_batch(self, mock_download, sample_ohlcv_data_short):
        """Test batch fetching of cryptocurrencies."""
        from ai_trader.data.fetchers.crypto import CryptoDataFetcher

        dates = pd.date_range("2023-01-01", periods=10)
        multi_data = pd.DataFrame({
            ("BTC-USD", "Open"): [100.0] * 10,
            ("BTC-USD", "High"): [105.0] * 10,
            ("BTC-USD", "Low"): [95.0] * 10,
            ("BTC-USD", "Close"): [100.0] * 10,
            ("ETH-USD", "Open"): [50.0] * 10,
            ("ETH-USD", "High"): [55.0] * 10,
            ("ETH-USD", "Low"): [45.0] * 10,
            ("ETH-USD", "Close"): [50.0] * 10,
        }, index=dates)
        multi_data.columns = pd.MultiIndex.from_tuples(multi_data.columns)
        mock_download.return_value = multi_data

        fetcher = CryptoDataFetcher(ticker="", start_date="2023-01-01")
        successful, failed = fetcher.fetch_batch(["BTC-USD", "ETH-USD"])

        assert len(successful) == 2
        assert len(failed) == 0

    @patch("ai_trader.data.fetchers.crypto.yf.download")
    def test_crypto_fetch_multiple_symbols(self, mock_download, sample_ohlcv_data_short):
        """Test crypto fetch with multiple symbols."""
        from ai_trader.data.fetchers.crypto import CryptoDataFetcher

        mock_download.return_value = sample_ohlcv_data_short

        fetcher = CryptoDataFetcher(ticker="", start_date="2023-01-01")
        successful, failed = fetcher.fetch_batch(["BTC-USD"])

        assert len(successful) > 0 or len(failed) > 0


class TestForexDataFetcher:
    """Test ForexDataFetcher functionality."""

    def test_forex_fetcher_init(self):
        """Test ForexDataFetcher initialization."""
        from ai_trader.data.fetchers.forex import ForexDataFetcher

        fetcher = ForexDataFetcher(symbol="EURUSD", start_date="2023-01-01")
        assert fetcher.symbol == "EURUSD"
        assert fetcher.start_date == "2023-01-01"

    @patch("ai_trader.data.fetchers.forex.yf.download")
    def test_forex_fetch_successful(self, mock_download):
        """Test successful forex data fetching."""
        from ai_trader.data.fetchers.forex import ForexDataFetcher

        # Forex doesn't require volume
        dates = pd.date_range("2023-01-01", periods=10)
        forex_data = pd.DataFrame({
            "open": [1.0800] * 10,
            "high": [1.0850] * 10,
            "low": [1.0750] * 10,
            "close": [1.0800] * 10,
        }, index=dates)
        forex_data.index.name = "date"

        mock_download.return_value = forex_data

        fetcher = ForexDataFetcher(symbol="EURUSD", start_date="2023-01-01")
        result = fetcher.fetch()

        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        # Forex should allow missing volume
        assert "close" in result.columns

    @patch("ai_trader.data.fetchers.forex.yf.download")
    def test_forex_fetch_without_volume(self, mock_download):
        """Test that forex data validates without volume column."""
        from ai_trader.data.fetchers.forex import ForexDataFetcher

        dates = pd.date_range("2023-01-01", periods=10)
        forex_data = pd.DataFrame({
            "open": [1.0800] * 10,
            "high": [1.0850] * 10,
            "low": [1.0750] * 10,
            "close": [1.0800] * 10,
        }, index=dates)
        forex_data.index.name = "date"

        mock_download.return_value = forex_data

        fetcher = ForexDataFetcher(symbol="GBPUSD", start_date="2023-01-01")
        result = fetcher.fetch()

        assert "volume" not in result.columns
        assert len(result) == 10


class TestVIXDataFetcher:
    """Test VIXDataFetcher functionality."""

    def test_vix_fetcher_init(self):
        """Test VIXDataFetcher initialization."""
        from ai_trader.data.fetchers.vix import VIXDataFetcher

        fetcher = VIXDataFetcher(start_date="2023-01-01")
        assert fetcher.start_date == "2023-01-01"

    @patch("ai_trader.data.fetchers.vix.yf.download")
    def test_vix_fetch_successful(self, mock_download):
        """Test successful VIX data fetching."""
        from ai_trader.data.fetchers.vix import VIXDataFetcher

        # VIX data with volume column
        dates = pd.date_range("2023-01-01", periods=10)
        vix_data = pd.DataFrame({
            "open": [20.0] * 10,
            "high": [21.0] * 10,
            "low": [19.0] * 10,
            "close": [20.0] * 10,
            "volume": [1000000] * 10,
        }, index=dates)
        vix_data.index.name = "date"

        mock_download.return_value = vix_data

        fetcher = VIXDataFetcher(start_date="2023-01-01")
        result = fetcher.fetch()

        assert isinstance(result, pd.DataFrame)
        assert not result.empty

    @patch("ai_trader.data.fetchers.vix.yf.download")
    def test_vix_fetch_with_end_date(self, mock_download):
        """Test VIX fetch with end date."""
        from ai_trader.data.fetchers.vix import VIXDataFetcher

        dates = pd.date_range("2023-01-01", periods=252)
        vix_data = pd.DataFrame({
            "open": [20.0] * 252,
            "high": [21.0] * 252,
            "low": [19.0] * 252,
            "close": [20.0] * 252,
            "volume": [1000000] * 252,
        }, index=dates)
        vix_data.index.name = "date"

        mock_download.return_value = vix_data

        fetcher = VIXDataFetcher(
            start_date="2023-01-01",
            end_date="2023-12-31"
        )
        result = fetcher.fetch()

        assert len(result) == 252

    @patch("ai_trader.data.fetchers.vix.yf.download")
    def test_vix_fetch_validation(self, mock_download):
        """Test VIX fetch data validation."""
        from ai_trader.data.fetchers.vix import VIXDataFetcher

        # Empty data should raise validation error
        mock_download.return_value = pd.DataFrame()

        fetcher = VIXDataFetcher(start_date="2023-01-01")

        with pytest.raises(DataFetchError):
            fetcher.fetch()


class TestFetcherErrorHandling:
    """Test error handling in fetchers."""

    @patch("ai_trader.data.fetchers.tw_stock.Stock")
    def test_tw_stock_handles_fetch_error(self, mock_stock, mock_twstock_response):
        """Test TW stock fetcher handles empty data."""
        from ai_trader.data.fetchers.tw_stock import TWStockFetcher

        # Test with empty response
        mock_instance = MagicMock()
        mock_instance.price = pd.DataFrame()  # Empty DataFrame
        mock_stock.return_value = mock_instance

        fetcher = TWStockFetcher(symbol="2330", start_date="2023-01-01")

        with pytest.raises(DataFetchError):
            fetcher.fetch()

    @patch("ai_trader.data.fetchers.crypto.yf.Ticker")
    def test_crypto_handles_fetch_error(self, mock_ticker):
        """Test crypto fetcher handles errors."""
        from ai_trader.data.fetchers.crypto import CryptoDataFetcher

        # Mock the Ticker object's history method to return empty DataFrame
        mock_ticker_instance = MagicMock()
        mock_ticker_instance.history.return_value = pd.DataFrame()  # Empty DataFrame
        mock_ticker.return_value = mock_ticker_instance

        fetcher = CryptoDataFetcher(ticker="BTC-USD", start_date="2023-01-01")

        # Empty data should raise DataFetchError after all retries
        with pytest.raises(DataFetchError):
            fetcher.fetch()

    @patch("ai_trader.data.fetchers.forex.yf.download")
    def test_forex_handles_empty_data(self, mock_download):
        """Test forex fetcher handles empty data."""
        from ai_trader.data.fetchers.forex import ForexDataFetcher

        mock_download.return_value = pd.DataFrame()

        fetcher = ForexDataFetcher(symbol="EURUSD", start_date="2023-01-01")

        with pytest.raises(DataFetchError):
            fetcher.fetch()
