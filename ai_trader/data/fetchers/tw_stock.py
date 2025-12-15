import warnings
from typing import Optional

import pandas as pd
from twstock import Stock

from ai_trader.core import DataFetchError, DataValidationError
from ai_trader.data.fetchers import BaseFetcher
from ai_trader.data.fetchers.base import logger

# Disable SSL warnings when we bypass verification
warnings.filterwarnings("ignore", message="Unverified HTTPS request")


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

    def __init__(self, symbol: str, start_date: str, end_date: Optional[str] = None):
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
            raise ValueError(f"Invalid start_date format: {start_date}. Expected YYYY-MM-DD") from e

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
            # Monkey-patch requests to disable SSL verification for twstock
            # This is necessary because Python 3.13+ has stricter SSL requirements
            # and TWSE certificates are missing Subject Key Identifier
            import requests

            original_get = requests.get

            def patched_get(*args, **kwargs):
                kwargs["verify"] = False
                return original_get(*args, **kwargs)

            requests.get = patched_get

            try:
                # Fetch from twstock
                stock = Stock(self.symbol)
                stock.fetch_from(year=self.start_year, month=self.start_month)
            finally:
                # Restore original requests.get
                requests.get = original_get

            if not stock.data:
                raise DataFetchError(
                    f"No data returned for {self.symbol}", symbol=self.symbol, source="twstock"
                )

            # Convert to DataFrame
            data_dicts = [d._asdict() for d in stock.data]
            df = pd.DataFrame(data_dicts)

            # twstock returns: date, capacity, turnover, open, high, low, close, change, transaction
            # We want: date (index), open, high, low, close, volume
            df = df[["date", "open", "high", "low", "close", "capacity"]]
            df = df.rename(columns={"capacity": "volume"})

            # Set date as index
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date")

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
                f"Network error fetching {self.symbol}: {e}", symbol=self.symbol, source="twstock"
            ) from e
        except Exception as e:
            if isinstance(e, (DataFetchError, DataValidationError)):
                raise
            raise DataFetchError(
                f"Failed to fetch {self.symbol}: {e}", symbol=self.symbol, source="twstock"
            ) from e

    def fetch_batch(self, symbols: list[str]) -> tuple[dict[str, pd.DataFrame], list[str]]:
        """
        Fetch data for multiple Taiwan stocks.

        Note: twstock library doesn't support batch operations, so this iterates
        through symbols sequentially. The SSL monkey-patch is applied once for
        all downloads to minimize overhead.

        Args:
            symbols: List of stock IDs (e.g., ['2330', '2317', '2454'])

        Returns:
            Tuple of (successful_data, failed_symbols):
            - successful_data: Dict mapping symbol -> DataFrame with OHLCV data
            - failed_symbols: List of symbols that failed to download

        Example:
            >>> fetcher = TWStockFetcher(symbol="", start_date="2020-01-01")
            >>> data, failed = fetcher.fetch_batch(['2330', '2317'])
            >>> print(f"Downloaded {len(data)} stocks, {len(failed)} failed")
        """
        if not symbols:
            logger.warning("fetch_batch called with empty symbol list")
            return {}, []

        logger.info(f"Fetching batch of {len(symbols)} TW stocks: {symbols}")

        successful_data = {}
        failed_symbols = []

        # Monkey-patch requests once for all downloads
        import requests

        original_get = requests.get

        def patched_get(*args, **kwargs):
            kwargs["verify"] = False
            return original_get(*args, **kwargs)

        requests.get = patched_get

        try:
            for symbol in symbols:
                try:
                    logger.debug(f"Fetching TW stock: {symbol}")

                    # Fetch from twstock
                    stock = Stock(symbol)
                    stock.fetch_from(year=self.start_year, month=self.start_month)

                    if not stock.data:
                        logger.warning(f"No data returned for {symbol}")
                        failed_symbols.append(symbol)
                        continue

                    # Convert to DataFrame
                    data_dicts = [d._asdict() for d in stock.data]
                    df = pd.DataFrame(data_dicts)

                    # Select and rename columns
                    df = df[["date", "open", "high", "low", "close", "capacity"]]
                    df = df.rename(columns={"capacity": "volume"})

                    # Set date as index
                    df["date"] = pd.to_datetime(df["date"])
                    df = df.set_index("date")

                    # Filter by end_date if provided
                    if self.end_date:
                        end_dt = pd.to_datetime(self.end_date)
                        df = df[df.index <= end_dt]

                    # Validate
                    self._validate_dataframe(df, symbol)

                    successful_data[symbol] = df
                    logger.info(
                        f"Successfully fetched {symbol}: {len(df)} rows "
                        f"from {df.index[0]} to {df.index[-1]}"
                    )

                except (ConnectionError, TimeoutError) as e:
                    logger.warning(f"Network error fetching {symbol}: {e}")
                    failed_symbols.append(symbol)
                except Exception as e:
                    logger.warning(f"Failed to fetch {symbol}: {e}")
                    failed_symbols.append(symbol)

        finally:
            # Always restore original requests.get
            requests.get = original_get
            logger.debug("Restored original requests.get")

        logger.info(
            f"Batch fetch complete: {len(successful_data)} succeeded, {len(failed_symbols)} failed"
        )

        return successful_data, failed_symbols
