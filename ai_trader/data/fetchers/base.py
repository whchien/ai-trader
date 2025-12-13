"""Base data fetcher for market data."""
import concurrent.futures
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Literal, Tuple, Optional

import pandas as pd
from twstock import Stock
import yfinance as yf

from ai_trader.core.logging import get_logger
from ai_trader.core.exceptions import (
    DataFetchError,
    DataValidationError,
    ConfigurationError,
)

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
        # Rename columns to lowercase
        df.columns = df.columns.str.lower()

        # Handle common variations
        column_mapping = {
            'adj close': 'adj_close',
            'capacity': 'volume'  # TW stock uses 'capacity'
        }
        df = df.rename(columns=column_mapping)

        # Ensure date is in the index
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')

        # Ensure index is named 'date'
        if df.index.name is None or df.index.name != 'date':
            df.index.name = 'date'

        return df

    def _validate_dataframe(self, df: pd.DataFrame, symbol: str) -> None:
        """
        Validate that DataFrame has required columns and data.

        Args:
            df: DataFrame to validate
            symbol: Stock symbol (for error messages)

        Raises:
            DataValidationError: If validation fails
        """
        if df.empty:
            raise DataValidationError(
                f"No data returned for {symbol}",
                symbol=symbol
            )

        # Check for required columns
        required = ['open', 'high', 'low', 'close', 'volume']
        df_cols = [col.lower() for col in df.columns]
        missing = [col for col in required if col not in df_cols]

        if missing:
            raise DataValidationError(
                f"Missing required columns for {symbol}: {missing}",
                symbol=symbol,
                issues=missing
            )

        logger.debug(f"Validated data for {symbol}: {len(df)} rows")


class USStockFetcher(BaseFetcher):
    """
    Fetches US stock market data from Yahoo Finance.

    Uses yfinance to download historical OHLCV data for US stocks.

    Attributes:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT', '^GSPC')
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format (None = today)

    Example:
        >>> fetcher = USStockFetcher(
        ...     symbol="AAPL",
        ...     start_date="2020-01-01",
        ...     end_date="2024-12-31"
        ... )
        >>> df = fetcher.fetch()
        >>> print(df.head())
    """

    def __init__(
        self,
        symbol: str,
        start_date: str,
        end_date: Optional[str] = None
    ):
        """
        Initialize US stock data fetcher.

        Args:
            symbol: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), defaults to today

        Raises:
            ValueError: If date format is invalid
        """
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date

        logger.info(
            f"Initialized USStockFetcher: symbol={symbol}, "
            f"start={start_date}, end={end_date or 'today'}"
        )

    def fetch(self) -> pd.DataFrame:
        """
        Fetch US stock data from Yahoo Finance.

        Returns:
            DataFrame with lowercase columns: ['open', 'high', 'low', 'close', 'volume']
            Index: DatetimeIndex named 'date'

        Raises:
            DataFetchError: If download fails
            DataValidationError: If data is invalid
        """
        logger.info(f"Fetching US stock data for {self.symbol}")

        try:
            # Download from yfinance
            df = yf.download(
                self.symbol,
                start=self.start_date,
                end=self.end_date,
                progress=False,
                auto_adjust=False  # Keep both Close and Adj Close
            )

            if df.empty:
                raise DataFetchError(
                    f"No data returned for {self.symbol}",
                    symbol=self.symbol,
                    source="yfinance"
                )

            # Reset index to make Date a column
            df = df.reset_index()

            # Normalize columns (yfinance returns: Date, Open, High, Low, Close, Adj Close, Volume)
            # We want: date (index), open, high, low, close, volume, adj_close
            df = self._normalize_columns(df)

            # Validate required columns exist
            self._validate_dataframe(df, self.symbol)

            logger.info(
                f"Successfully fetched {len(df)} rows for {self.symbol} "
                f"from {df.index[0]} to {df.index[-1]}"
            )

            return df

        except (ConnectionError, TimeoutError) as e:
            raise DataFetchError(
                f"Network error fetching {self.symbol}: {e}",
                symbol=self.symbol,
                source="yfinance"
            ) from e
        except Exception as e:
            if isinstance(e, (DataFetchError, DataValidationError)):
                raise
            raise DataFetchError(
                f"Failed to fetch {self.symbol}: {e}",
                symbol=self.symbol,
                source="yfinance"
            ) from e


class TWStockFetcher(BaseFetcher):
    """
    Fetches Taiwan stock market data from twstock library.

    Uses twstock to download historical OHLCV data for Taiwan stocks.

    Attributes:
        symbol: Stock ID (e.g., '2330' for TSMC)
        start_date: Start date in YYYY-MM-DD format
        end_date: End date (not used by twstock, included for API consistency)

    Note:
        twstock fetches from start_date to present. The end_date parameter
        is accepted for API consistency but will be used to filter results.

    Example:
        >>> fetcher = TWStockFetcher(
        ...     symbol="2330",
        ...     start_date="2020-01-01"
        ... )
        >>> df = fetcher.fetch()
        >>> print(df.head())
    """

    def __init__(
        self,
        symbol: str,
        start_date: str,
        end_date: Optional[str] = None
    ):
        """
        Initialize Taiwan stock data fetcher.

        Args:
            symbol: Stock ID (e.g., '2330')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), used for filtering

        Raises:
            ValueError: If date format is invalid
        """
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date

        # Parse start_date to get year and month for twstock
        try:
            from datetime import datetime
            dt = datetime.strptime(start_date, "%Y-%m-%d")
            self.start_year = dt.year
            self.start_month = dt.month
        except ValueError as e:
            raise ValueError(
                f"Invalid start_date format: {start_date}. Expected YYYY-MM-DD"
            ) from e

        logger.info(
            f"Initialized TWStockFetcher: symbol={symbol}, "
            f"start={start_date}, end={end_date or 'present'}"
        )

    def fetch(self) -> pd.DataFrame:
        """
        Fetch Taiwan stock data from twstock.

        Returns:
            DataFrame with lowercase columns: ['open', 'high', 'low', 'close', 'volume']
            Index: DatetimeIndex named 'date'

        Raises:
            DataFetchError: If download fails
            DataValidationError: If data is invalid
        """
        logger.info(f"Fetching TW stock data for {self.symbol}")

        try:
            # Fetch from twstock
            stock = Stock(self.symbol)
            stock.fetch_from(year=self.start_year, month=self.start_month)

            if not stock.data:
                raise DataFetchError(
                    f"No data returned for {self.symbol}",
                    symbol=self.symbol,
                    source="twstock"
                )

            # Convert to DataFrame
            data_dicts = [d._asdict() for d in stock.data]
            df = pd.DataFrame(data_dicts)

            # twstock returns: date, capacity, turnover, open, high, low, close, change, transaction
            # We want: date (index), open, high, low, close, volume
            df = df[["date", "open", "high", "low", "close", "capacity"]]
            df = df.rename(columns={"capacity": "volume"})

            # Set date as index
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')

            # Filter by end_date if provided
            if self.end_date:
                end_dt = pd.to_datetime(self.end_date)
                df = df[df.index <= end_dt]

            # Validate
            self._validate_dataframe(df, self.symbol)

            logger.info(
                f"Successfully fetched {len(df)} rows for {self.symbol} "
                f"from {df.index[0]} to {df.index[-1]}"
            )

            return df

        except (ConnectionError, TimeoutError) as e:
            raise DataFetchError(
                f"Network error fetching {self.symbol}: {e}",
                symbol=self.symbol,
                source="twstock"
            ) from e
        except Exception as e:
            if isinstance(e, (DataFetchError, DataValidationError)):
                raise
            raise DataFetchError(
                f"Failed to fetch {self.symbol}: {e}",
                symbol=self.symbol,
                source="twstock"
            ) from e


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
    datapath = {
        "tw": "data/tw_stock/2330.csv",
        "us": "data/us_stock/tsm.csv"
    }

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
