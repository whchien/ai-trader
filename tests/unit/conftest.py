"""Unit test fixtures and configuration."""

import pytest
from unittest.mock import MagicMock, Mock
import pandas as pd


@pytest.fixture
def mock_yfinance_response():
    """Mock yfinance.download() response with proper structure."""
    dates = pd.date_range(start="2023-01-01", periods=252, freq="D")
    data = {
        "Date": dates,
        "Open": [100 + i * 0.1 for i in range(252)],
        "High": [102 + i * 0.1 for i in range(252)],
        "Low": [98 + i * 0.1 for i in range(252)],
        "Close": [101 + i * 0.1 for i in range(252)],
        "Adj Close": [101 + i * 0.1 for i in range(252)],
        "Volume": [1000000] * 252,
    }
    df = pd.DataFrame(data)
    df = df.set_index("Date")
    return df


@pytest.fixture
def mock_yf_download():
    """Callable mock for yfinance.download with symbol-based response logic."""
    def _mock_download(symbol, start, end, progress=False, auto_adjust=False, group_by=None):
        # Return empty DataFrame for invalid symbols
        if symbol in ["INVALID", "ERROR", "NOTFOUND"]:
            return pd.DataFrame()

        # Generate date range from start to end
        try:
            dates = pd.date_range(start=start, end=end, freq="D")
        except:
            dates = pd.date_range(start="2023-01-01", periods=252, freq="D")

        num_dates = len(dates)
        data = {
            "Date": dates,
            "Open": [100.0] * num_dates,
            "High": [105.0] * num_dates,
            "Low": [95.0] * num_dates,
            "Close": [100.0] * num_dates,
            "Adj Close": [100.0] * num_dates,
            "Volume": [1000000] * num_dates,
        }
        df = pd.DataFrame(data)
        df = df.set_index("Date")
        return df

    return _mock_download


@pytest.fixture
def mock_yf_download_multiindex():
    """Mock yfinance.download for multiple symbols with MultiIndex columns."""
    def _mock_download_multi(symbols_str, start, end, progress=False, auto_adjust=False, group_by=None):
        symbols = symbols_str.split()
        dates = pd.date_range(start=start, end=end, freq="D")
        num_dates = len(dates)

        # Create MultiIndex columns (symbol, column_name)
        columns = pd.MultiIndex.from_product(
            [symbols, ["Open", "High", "Low", "Close", "Adj Close", "Volume"]]
        )

        # Create data for all symbols
        data = {}
        for symbol in symbols:
            for col in ["Open", "High", "Low", "Close", "Adj Close", "Volume"]:
                if col == "Volume":
                    data[(symbol, col)] = [1000000] * num_dates
                elif col == "High":
                    data[(symbol, col)] = [105.0] * num_dates
                elif col == "Low":
                    data[(symbol, col)] = [95.0] * num_dates
                else:
                    data[(symbol, col)] = [100.0] * num_dates

        df = pd.DataFrame(data, index=dates)
        df.index.name = "Date"
        return df

    return _mock_download_multi


@pytest.fixture
def mock_twstock_response():
    """Mock twstock fetcher response structure."""
    dates = pd.date_range(start="2023-01-01", periods=252, freq="D")
    data = {
        "date": dates,
        "open": [100 + i * 0.1 for i in range(252)],
        "high": [102 + i * 0.1 for i in range(252)],
        "low": [98 + i * 0.1 for i in range(252)],
        "close": [101 + i * 0.1 for i in range(252)],
        "capacity": [1000000] * 252,  # TW stock uses 'capacity' instead of 'volume'
    }
    df = pd.DataFrame(data)
    df = df.set_index("date")
    return df


@pytest.fixture
def mock_twstock_stock(mock_twstock_response):
    """Mock twstock.Stock class."""
    mock_stock = MagicMock()
    mock_stock.fetch_from.return_value = True

    # Convert DataFrame to list of MagicMock objects (simulating twstock.Stock.data)
    data_objects = []
    for idx, row in mock_twstock_response.iterrows():
        mock_obj = MagicMock()
        mock_obj.date = idx
        mock_obj.open = row["open"]
        mock_obj.high = row["high"]
        mock_obj.low = row["low"]
        mock_obj.close = row["close"]
        mock_obj.capacity = row["capacity"]
        data_objects.append(mock_obj)

    mock_stock.data = data_objects
    return mock_stock


@pytest.fixture
def mock_sleep():
    """Mock time.sleep to speed up retry logic tests."""
    from unittest.mock import patch
    with patch("time.sleep"):
        yield


@pytest.fixture
def mock_yfinance(mock_yf_download):
    """Patch yfinance.download globally for unit tests."""
    from unittest.mock import patch
    with patch("yfinance.download", side_effect=mock_yf_download) as mock:
        yield mock


@pytest.fixture
def mock_twstock(mock_twstock_stock):
    """Patch twstock.Stock globally for unit tests."""
    from unittest.mock import patch
    with patch("twstock.Stock", return_value=mock_twstock_stock) as mock:
        yield mock


@pytest.fixture
def mock_csv_operations(sample_ohlcv_data_short, tmp_path):
    """Mock CSV read/write operations."""
    from unittest.mock import patch, MagicMock

    def mock_read_csv(filepath, *args, **kwargs):
        # Return sample data for any CSV read
        return sample_ohlcv_data_short.copy()

    def mock_to_csv(df, filepath, *args, **kwargs):
        # Simulate writing by doing nothing
        pass

    with patch("pandas.read_csv", side_effect=mock_read_csv):
        with patch("pandas.DataFrame.to_csv", side_effect=mock_to_csv):
            yield


@pytest.fixture
def reset_logging():
    """Reset logging configuration between tests to avoid interference."""
    import logging

    yield

    # Clear all handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
