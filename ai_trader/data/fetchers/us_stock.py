from typing import Optional

import pandas as pd
import yfinance as yf

from ai_trader.core import DataFetchError, DataValidationError
from ai_trader.data.fetchers import BaseFetcher
from ai_trader.data.fetchers.base import logger


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
