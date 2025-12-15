"""Base data fetcher for market data."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Literal

import pandas as pd

from ai_trader.core.exceptions import DataValidationError
from ai_trader.core.logging import get_logger

logger = get_logger(__name__)


class BaseFetcher(ABC):
    """Abstract base class for data fetchers."""

    @abstractmethod
    def fetch(self) -> pd.DataFrame:
        """
        Fetch market data.

        Returns:
            DataFrame with standardized OHLCV data:
            - Index: DatetimeIndex named 'date'
            - Columns: ['open', 'high', 'low', 'close', 'volume'] (lowercase)
            - All column names MUST be lowercase

        Raises:
            DataFetchError: If fetching fails
            DataValidationError: If data is invalid
        """
        pass

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize column names to lowercase standard.

        Args:
            df: DataFrame with any case columns

        Returns:
            DataFrame with lowercase column names and date index
        """
        # Handle MultiIndex columns (from yfinance when downloading single ticker)
        if isinstance(df.columns, pd.MultiIndex):
            # For single ticker, flatten to just the column names (first level)
            df.columns = df.columns.get_level_values(0)

        # Rename columns to lowercase
        df.columns = df.columns.str.lower()

        # Handle common variations
        column_mapping = {
            "adj close": "adj_close",
            "capacity": "volume",  # TW stock uses 'capacity'
        }
        df = df.rename(columns=column_mapping)

        # Ensure date is in the index
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date")

        # Ensure index is named 'date'
        if df.index.name is None or df.index.name != "date":
            df.index.name = "date"

        return df

    def _validate_dataframe(self, df: pd.DataFrame, symbol: str, skip_volume: bool = False) -> None:
        """
        Validate that DataFrame has required columns and data.

        Args:
            df: DataFrame to validate
            symbol: Stock symbol (for error messages)
            skip_volume: If True, don't require volume data (for forex)

        Raises:
            DataValidationError: If validation fails
        """
        if df.empty:
            raise DataValidationError(f"No data returned for {symbol}", symbol=symbol)

        # Check for required columns
        required = ["open", "high", "low", "close"]
        if not skip_volume:
            required.append("volume")

        df_cols = [col.lower() for col in df.columns]
        missing = [col for col in required if col not in df_cols]

        if missing:
            raise DataValidationError(
                f"Missing required columns for {symbol}: {missing}", symbol=symbol, issues=missing
            )

        logger.debug(f"Validated data for {symbol}: {len(df)} rows")


def load_example(market: Literal["us", "tw"] = "tw") -> pd.DataFrame:
    """
    Load example data for the specified market.

    Args:
        market: Market type ('us' or 'tw')

    Returns:
        DataFrame with example stock data

    Raises:
        ValueError: If market is invalid
        FileNotFoundError: If example data file doesn't exist

    Example:
        >>> df = load_example(market="tw")
        >>> print(df.head())
    """
    datapath = {"tw": "data/tw_stock/2330.csv", "us": "data/us_stock/tsm.csv"}

    if market not in datapath:
        raise ValueError(f"Market only supports 'tw' or 'us', got '{market}'")

    # Both markets now use lowercase 'date' column
    date_col = "date"
    file_path = Path(datapath[market])

    if not file_path.exists():
        raise FileNotFoundError(f"Example data file not found: {file_path}")

    df = pd.read_csv(
        file_path,
        parse_dates=[date_col],
        index_col=[date_col],
    )

    logger.info(f"Loaded example data for {market} market: {len(df)} rows")
    return df
