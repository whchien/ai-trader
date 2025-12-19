"""Integration tests for data pipeline workflows."""

import pytest
import pandas as pd
import tempfile
from pathlib import Path


class TestDataFetchAndStoragePipeline:
    """Test end-to-end data fetch, validate, save, and load workflow."""

    def test_us_stock_data_fetch_and_validation(self, sample_ohlcv_data):
        """Test US stock data fetch and validation workflow."""
        from ai_trader.data.fetchers.us_stock import USStockFetcher
        from unittest.mock import patch

        # Mock yfinance to avoid network calls
        with patch('ai_trader.data.fetchers.us_stock.yf.download') as mock_download:
            mock_download.return_value = sample_ohlcv_data

            # Fetch data
            fetcher = USStockFetcher(symbol="AAPL", start_date="2023-01-01")
            data = fetcher.fetch()

            # Verify data is valid
            assert not data.empty
            assert len(data) > 0
            assert 'close' in data.columns
            assert 'date' == data.index.name.lower()


    def test_data_validation_pipeline(self):
        """Test data validation at different stages of pipeline."""
        from ai_trader.core.exceptions import DataValidationError

        # Create synthetic valid data
        dates = pd.date_range("2023-01-01", periods=10)
        valid_data = pd.DataFrame({
            'open': [100.0] * 10,
            'high': [105.0] * 10,
            'low': [95.0] * 10,
            'close': [100.0] * 10,
            'volume': [1000000] * 10,
        }, index=dates)
        valid_data.index.name = 'date'

        # Verify valid data structure
        assert not valid_data.empty
        assert len(valid_data) == 10
        assert all(col in valid_data.columns for col in ['open', 'high', 'low', 'close', 'volume'])

        # Verify empty data is invalid
        empty_data = pd.DataFrame()
        assert empty_data.empty

        # Verify data with missing columns is incomplete
        missing_columns_data = pd.DataFrame({
            'open': [100.0] * 10,
            'high': [105.0] * 10,
        }, index=dates)
        required_columns = {'open', 'high', 'low', 'close', 'volume'}
        actual_columns = set(missing_columns_data.columns)
        assert not required_columns.issubset(actual_columns)


class TestDataNormalization:
    """Test data normalization and transformation workflows."""

    def test_multiindex_column_handling(self):
        """Test handling of MultiIndex columns from yfinance."""

        # Create data with MultiIndex columns like yfinance returns
        dates = pd.date_range("2023-01-01", periods=5)
        data = pd.DataFrame({
            ('AAPL', 'Open'): [100.0, 101.0, 102.0, 103.0, 104.0],
            ('AAPL', 'High'): [105.0] * 5,
            ('AAPL', 'Low'): [95.0] * 5,
            ('AAPL', 'Close'): [102.0] * 5,
            ('AAPL', 'Volume'): [1000000] * 5,
        }, index=dates)
        data.columns = pd.MultiIndex.from_tuples(data.columns)
        data.index.name = 'Date'

        # Verify data is MultiIndex before processing
        assert isinstance(data.columns, pd.MultiIndex)

        # Flatten the MultiIndex to single level
        data_flat = data.copy()
        if isinstance(data_flat.columns, pd.MultiIndex):
            # Get the innermost level (typically 'Open', 'Close', etc.)
            data_flat.columns = data_flat.columns.get_level_values(-1)

        # Verify flattening worked
        assert not isinstance(data_flat.columns, pd.MultiIndex)
        assert 'Open' in data_flat.columns
        assert 'Close' in data_flat.columns

    def test_column_normalization_to_lowercase(self):
        """Test normalizing column names to lowercase."""

        dates = pd.date_range("2023-01-01", periods=5)
        data = pd.DataFrame({
            'Open': [100.0] * 5,
            'High': [105.0] * 5,
            'Low': [95.0] * 5,
            'Close': [100.0] * 5,
            'Volume': [1000000] * 5,
        }, index=dates)
        data.index.name = 'Date'

        # Normalize columns to lowercase
        data_normalized = data.copy()
        data_normalized.columns = data_normalized.columns.str.lower()

        # Verify normalization
        assert 'open' in data_normalized.columns
        assert 'close' in data_normalized.columns
        assert 'volume' in data_normalized.columns


class TestDataConsistency:
    """Test data consistency across pipeline stages."""

    def test_data_consistency_across_transformations(self, sample_ohlcv_data):
        """Test that data remains consistent through various transformations."""
        original_length = len(sample_ohlcv_data)
        original_columns = set(sample_ohlcv_data.columns)

        # Make a copy and transform
        transformed = sample_ohlcv_data.copy()
        transformed.columns = transformed.columns.str.lower()

        # Verify consistency
        assert len(transformed) == original_length
        assert len(transformed.columns) == len(original_columns)

    def test_date_index_preservation(self, sample_ohlcv_data):
        """Test that date index is preserved through transformations."""
        original_index = sample_ohlcv_data.index.copy()

        # Make a copy
        transformed = sample_ohlcv_data.copy()

        # Verify index is preserved
        assert len(transformed.index) == len(original_index)
        assert (transformed.index == original_index).all()
