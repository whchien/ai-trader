"""Root-level pytest configuration and shared fixtures for all tests."""

import pandas as pd
import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil

# Test data paths
TEST_ROOT = Path(__file__).parent
FIXTURES_DIR = TEST_ROOT / "fixtures"
SAMPLE_DATA_DIR = FIXTURES_DIR / "sample_data"


@pytest.fixture(scope="session")
def test_data_dir():
    """Fixture for test data directory."""
    SAMPLE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    return SAMPLE_DATA_DIR


@pytest.fixture(scope="function")
def temp_dir():
    """Create temporary directory for test outputs."""
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def sample_ohlcv_data():
    """Generate sample OHLCV DataFrame with realistic date range."""
    dates = pd.date_range(start="2020-01-01", end="2023-12-31", freq="D")
    data = {
        "open": [100 + i * 0.1 for i in range(len(dates))],
        "high": [102 + i * 0.1 for i in range(len(dates))],
        "low": [98 + i * 0.1 for i in range(len(dates))],
        "close": [101 + i * 0.1 for i in range(len(dates))],
        "volume": [1000000 + i * 1000 for i in range(len(dates))],
    }
    df = pd.DataFrame(data, index=dates)
    df.index.name = "date"
    return df


@pytest.fixture
def sample_ohlcv_data_short():
    """Generate short OHLCV DataFrame (100 days) for faster tests."""
    dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
    data = {
        "open": [100 + i * 0.1 for i in range(len(dates))],
        "high": [102 + i * 0.1 for i in range(len(dates))],
        "low": [98 + i * 0.1 for i in range(len(dates))],
        "close": [101 + i * 0.1 for i in range(len(dates))],
        "volume": [1000000 + i * 1000 for i in range(len(dates))],
    }
    df = pd.DataFrame(data, index=dates)
    df.index.name = "date"
    return df


@pytest.fixture
def sample_config_dict():
    """Sample configuration dictionary for Config tests."""
    return {
        "data": {
            "market": "tw",
            "start_year": 2020,
            "start_month": 1,
            "data_dir": "./data/tw_stock/"
        },
        "broker": {
            "cash": 1000000,
            "commission": 0.001425,
            "stake": 0.95
        },
        "backtest": {
            "start_date": "2020-01-01",
            "end_date": "2023-12-31"
        }
    }


@pytest.fixture
def sample_config_dict_us():
    """Sample US market configuration dictionary."""
    return {
        "data": {
            "market": "us",
            "start_year": 2020,
            "start_month": 1,
            "data_dir": "./data/us_stock/"
        },
        "broker": {
            "cash": 100000,
            "commission": 0.001,
            "stake": 0.90
        },
        "backtest": {
            "start_date": "2021-01-01",
            "end_date": "2023-12-31"
        }
    }
