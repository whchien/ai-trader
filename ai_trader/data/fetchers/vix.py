from typing import Optional

import pandas as pd
import yfinance as yf

from ai_trader.core import DataFetchError, DataValidationError
from ai_trader.data.fetchers import BaseFetcher
from ai_trader.data.fetchers.base import logger


class VIXDataFetcher(BaseFetcher):
    """
    Fetches CBOE Volatility Index (VIX) data from Yahoo Finance.

    Uses yfinance to download historical OHLCV data for the VIX index.

    The VIX is a real-time index representing the market's expectation
    of 30-day forward-looking volatility. It's calculated from S&P 500
    index options and is often referred to as the "fear gauge".

    Attributes:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format (None = today)
        symbol: Fixed to '^VIX' (CBOE Volatility Index)

    Note:
        VIX is not directly tradeable. It's traded indirectly through:
        - VIX futures contracts
        - VIX options
        - ETNs/ETFs like VXX, UVXY

    Example:
        >>> fetcher = VIXDataFetcher(
        ...     start_date="2020-01-01",
        ...     end_date="2024-12-31"
        ... )
        >>> df = fetcher.fetch()
        >>> print(df.head())
        >>> print(f"VIX range: {df['close'].min():.2f} - {df['close'].max():.2f}")
    """

    VIX_SYMBOL = "^VIX"

    def __init__(
        self,
        start_date: str,
        end_date: Optional[str] = None
    ):
        """
        Initialize VIX data fetcher.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), defaults to today

        Raises:
            ValueError: If date format is invalid
        """
        self.symbol = self.VIX_SYMBOL
        self.start_date = start_date
        self.end_date = end_date

        logger.info(
            f"Initialized VIXDataFetcher: "
            f"start={start_date}, end={end_date or 'today'}"
        )

    def fetch(self) -> pd.DataFrame:
        """
        Fetch VIX index data from Yahoo Finance.

        Returns:
            DataFrame with lowercase columns: ['open', 'high', 'low', 'close', 'volume']
            Index: DatetimeIndex named 'date'

        Raises:
            DataFetchError: If download fails
            DataValidationError: If data is invalid
        """
        logger.info(f"Fetching VIX index data")

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
                    f"No data returned for VIX index",
                    symbol=self.symbol,
                    source="yfinance"
                )

            # Reset index to make Date a column
            df = df.reset_index()

            # Normalize columns to lowercase
            df = self._normalize_columns(df)

            # Validate (VIX has real volume data)
            self._validate_dataframe(df, self.symbol)

            logger.info(
                f"Successfully fetched {len(df)} rows for VIX "
                f"from {df.index[0]} to {df.index[-1]}"
            )

            return df

        except (ConnectionError, TimeoutError) as e:
            raise DataFetchError(
                f"Network error fetching VIX: {e}",
                symbol=self.symbol,
                source="yfinance"
            ) from e
        except Exception as e:
            if isinstance(e, (DataFetchError, DataValidationError)):
                raise
            raise DataFetchError(
                f"Failed to fetch VIX: {e}",
                symbol=self.symbol,
                source="yfinance"
            ) from e
