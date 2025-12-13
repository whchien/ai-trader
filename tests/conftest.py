"""Shared test fixtures and configuration."""
import pytest
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta


@pytest.fixture
def sample_stock_data():
    """Create sample stock data for testing."""
    dates = pd.date_range(start="2020-01-01", end="2020-12-31", freq="D")
    data = pd.DataFrame({
        "Date": dates,
        "Open": 100 + pd.Series(range(len(dates))) * 0.1,
        "High": 102 + pd.Series(range(len(dates))) * 0.1,
        "Low": 98 + pd.Series(range(len(dates))) * 0.1,
        "Close": 101 + pd.Series(range(len(dates))) * 0.1,
        "Volume": 1000000 + pd.Series(range(len(dates))) * 1000,
    })
    data["Date"] = pd.to_datetime(data["Date"])
    return data


@pytest.fixture
def sample_tw_stock_data():
    """Create sample Taiwan stock data (lowercase columns)."""
    dates = pd.date_range(start="2020-01-01", end="2020-12-31", freq="D")
    data = pd.DataFrame({
        "date": dates,
        "open": 100 + pd.Series(range(len(dates))) * 0.1,
        "high": 102 + pd.Series(range(len(dates))) * 0.1,
        "low": 98 + pd.Series(range(len(dates))) * 0.1,
        "close": 101 + pd.Series(range(len(dates))) * 0.1,
        "volume": 1000000 + pd.Series(range(len(dates))) * 1000,
    })
    data["date"] = pd.to_datetime(data["date"])
    return data


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary directory for test data."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def sample_csv_file(temp_data_dir, sample_stock_data):
    """Create a sample CSV file for testing."""
    csv_path = temp_data_dir / "TEST.csv"
    sample_stock_data.to_csv(csv_path, index=False)
    return csv_path


@pytest.fixture
def trader_config():
    """Sample trader configuration."""
    return {
        "cash": 1000000,
        "commission": 0.001425,
        "start_date": "2020-01-01",
        "end_date": "2020-12-31",
    }
