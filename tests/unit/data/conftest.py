"""Data module specific fixtures for fetchers and storage."""

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd


@pytest.fixture
def sample_fetcher_data():
    """Generate sample data for fetcher tests."""
    dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
    return pd.DataFrame({
        "open": [100.0] * len(dates),
        "high": [105.0] * len(dates),
        "low": [95.0] * len(dates),
        "close": [100.0] * len(dates),
        "volume": [1000000] * len(dates),
    }, index=dates)


@pytest.fixture
def yf_multiindex_data():
    """Sample yfinance response with MultiIndex columns (for batch operations)."""
    dates = pd.date_range(start="2023-01-01", periods=50, freq="D")
    symbols = ["AAPL", "MSFT"]

    columns = pd.MultiIndex.from_product(
        [symbols, ["Open", "High", "Low", "Close", "Adj Close", "Volume"]]
    )

    data = {}
    for symbol in symbols:
        for col in ["Open", "High", "Low", "Close", "Adj Close", "Volume"]:
            if col == "Volume":
                data[(symbol, col)] = [1000000] * len(dates)
            elif col == "High":
                data[(symbol, col)] = [105.0] * len(dates)
            elif col == "Low":
                data[(symbol, col)] = [95.0] * len(dates)
            else:
                data[(symbol, col)] = [100.0] * len(dates)

    df = pd.DataFrame(data, index=dates)
    df.index.name = "Date"
    return df


@pytest.fixture
def invalid_data_frames():
    """Collection of invalid DataFrames for validation testing."""
    return {
        "empty": pd.DataFrame(),
        "missing_columns": pd.DataFrame({
            "open": [100.0],
            "high": [105.0],
            # missing low, close, volume
        }),
        "missing_volume": pd.DataFrame({
            "open": [100.0],
            "high": [105.0],
            "low": [95.0],
            "close": [100.0],
        }),
        "all_nan": pd.DataFrame({
            "open": [float("nan")] * 10,
            "high": [float("nan")] * 10,
            "low": [float("nan")] * 10,
            "close": [float("nan")] * 10,
            "volume": [float("nan")] * 10,
        }),
    }


@pytest.fixture
def mock_yfinance_patched(mock_yf_download):
    """Patch yfinance.download for data module tests."""
    with patch("ai_trader.data.fetchers.us_stock.yf.download", side_effect=mock_yf_download) as mock:
        yield mock


@pytest.fixture
def mock_twstock_patched(mock_twstock_stock):
    """Patch twstock.Stock for data module tests."""
    with patch("ai_trader.data.fetchers.tw_stock.twstock.Stock", return_value=mock_twstock_stock) as mock:
        yield mock


@pytest.fixture
def file_manager_temp_dir(tmp_path):
    """Temporary directory configured for FileManager tests."""
    data_dir = tmp_path / "market_data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


@pytest.fixture
def mock_file_operations(tmp_path):
    """Mock file system operations for storage tests."""
    from pathlib import Path

    class MockFileManager:
        def __init__(self, base_dir):
            self.base_dir = Path(base_dir)

        def save_data(self, df, filename):
            path = self.base_dir / filename
            df.to_csv(path)
            return path

        def load_data(self, filename):
            path = self.base_dir / filename
            if not path.exists():
                raise FileNotFoundError(f"File not found: {path}")
            return pd.read_csv(path, index_col=0, parse_dates=True)

    return MockFileManager(tmp_path)
