from typing import Optional

import pandas as pd
import yfinance as yf

from ai_trader.core import DataFetchError, DataValidationError
from ai_trader.data.fetchers import BaseFetcher
from ai_trader.data.fetchers.base import logger


class ForexDataFetcher(BaseFetcher):
    """
    Fetches foreign exchange (forex/FX) data from Yahoo Finance.

    Uses yfinance to download historical OHLCV data for currency pairs.

    Note:
        Forex data has zero volume because the forex market is decentralized
        with no centralized exchange providing volume data.

    Attributes:
        symbol: Forex pair ticker symbol (e.g., 'EURUSD=X', 'JPY=X', 'GBPUSD=X')
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format (None = today)

    Common FX Pairs:
        - EUR/USD: 'EURUSD=X'
        - GBP/USD: 'GBPUSD=X'
        - USD/JPY: 'JPY=X'
        - USD/CHF: 'CHF=X'
        - USD/CAD: 'CAD=X'
        - AUD/USD: 'AUDUSD=X'

    Example:
        >>> fetcher = ForexDataFetcher(
        ...     symbol="EURUSD=X",
        ...     start_date="2020-01-01",
        ...     end_date="2024-12-31"
        ... )
        >>> df = fetcher.fetch()
        >>> print(df.head())
    """

    def __init__(self, symbol: str, start_date: str, end_date: Optional[str] = None):
        """
        Initialize forex data fetcher.

        Args:
            symbol: Forex pair ticker symbol (e.g., 'EURUSD=X')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), defaults to today

        Raises:
            ValueError: If date format is invalid
        """
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date

        logger.info(
            f"Initialized ForexDataFetcher: symbol={symbol}, "
            f"start={start_date}, end={end_date or 'today'}"
        )

    def fetch(self) -> pd.DataFrame:
        """
        Fetch forex data from Yahoo Finance.

        Returns:
            DataFrame with lowercase columns: ['open', 'high', 'low', 'close', 'volume']
            Index: DatetimeIndex named 'date'
            Note: volume will be 0 for all rows (forex has no centralized volume data)

        Raises:
            DataFetchError: If download fails
            DataValidationError: If data is invalid
        """
        logger.info(f"Fetching forex data for {self.symbol}")

        try:
            # Download from yfinance
            df = yf.download(
                self.symbol,
                start=self.start_date,
                end=self.end_date,
                progress=False,
                auto_adjust=False,  # Keep both Close and Adj Close
            )

            if df.empty:
                raise DataFetchError(
                    f"No data returned for {self.symbol}", symbol=self.symbol, source="yfinance"
                )

            # Reset index to make Date a column
            df = df.reset_index()

            # Normalize columns to lowercase
            df = self._normalize_columns(df)

            # Validate (skip volume check since forex volume is always 0)
            self._validate_dataframe(df, self.symbol, skip_volume=True)

            logger.info(
                f"Successfully fetched {len(df)} rows for {self.symbol} "
                f"from {df.index[0]} to {df.index[-1]}"
            )
            logger.debug(
                f"Note: Volume data is 0 for forex pair {self.symbol} "
                f"(forex market is decentralized)"
            )

            return df

        except (ConnectionError, TimeoutError) as e:
            raise DataFetchError(
                f"Network error fetching {self.symbol}: {e}", symbol=self.symbol, source="yfinance"
            ) from e
        except Exception as e:
            if isinstance(e, (DataFetchError, DataValidationError)):
                raise
            raise DataFetchError(
                f"Failed to fetch {self.symbol}: {e}", symbol=self.symbol, source="yfinance"
            ) from e
