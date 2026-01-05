import time
import warnings
from collections import namedtuple
from typing import Optional

import pandas as pd
from twstock import Stock

from ai_trader.core import DataFetchError, DataValidationError
from ai_trader.core.logging import get_logger
from ai_trader.data.fetchers import BaseFetcher

logger = get_logger(__name__)

# Disable SSL warnings when we bypass verification
warnings.filterwarnings("ignore", message="Unverified HTTPS request")


# Monkey-patch twstock to handle the new 10-field format from Taiwan Stock Exchange API
# The API now returns an additional "notes" field (註記) making it 10 fields instead of 9
# This patch updates the DATATUPLE and related fetcher classes to handle this new format
def _patch_twstock_for_new_api():
    """
    Patch twstock library to support the new Taiwan Stock Exchange API format.

    The TWSE API now returns 10 fields instead of 9:
    - Old: date, capacity, turnover, open, high, low, close, change, transaction (9 fields)
    - New: date, capacity, turnover, open, high, low, close, change, transaction, notes (10 fields)
    """
    import datetime

    import twstock.stock

    # Update the DATATUPLE to include the new 'notes' field
    if not hasattr(twstock.stock, "_patched_datatuple"):
        # Create new DATATUPLE with the notes field
        twstock.stock.DATATUPLE = namedtuple(
            "Data",
            [
                "date",
                "capacity",
                "turnover",
                "open",
                "high",
                "low",
                "close",
                "change",
                "transaction",
                "notes",  # New field from API
            ],
        )

        # Patch TWSEFetcher._make_datatuple to completely replace the method
        def patched_tws_make_datatuple(self, data):
            """
            Convert raw API data to DATATUPLE, handling the new 10-field format.
            """
            # Extract the notes field if present (index 9)
            notes = data[9] if len(data) > 9 else ""

            # Process the first 9 fields as the original method did
            data = data[:9]

            # Convert date format: '114/01/02' -> '2025/01/02'
            data[0] = datetime.datetime.strptime(self._convert_date(data[0]), "%Y/%m/%d")
            # Convert capacity to int (remove commas)
            data[1] = int(data[1].replace(",", ""))
            # Convert turnover to int (remove commas)
            data[2] = int(data[2].replace(",", ""))
            # Convert prices (handle "--" for missing data)
            data[3] = None if data[3] == "--" else float(data[3].replace(",", ""))
            data[4] = None if data[4] == "--" else float(data[4].replace(",", ""))
            data[5] = None if data[5] == "--" else float(data[5].replace(",", ""))
            data[6] = None if data[6] == "--" else float(data[6].replace(",", ""))
            # Convert change (handle X marking as 0)
            data[7] = float(
                0.0 if data[7].replace(",", "") == "X0.00" else data[7].replace(",", "")
            )
            # Convert transaction count to int (remove commas)
            data[8] = int(data[8].replace(",", ""))

            # Return new DATATUPLE with the notes field
            return twstock.stock.DATATUPLE(
                data[0],
                data[1],
                data[2],
                data[3],
                data[4],
                data[5],
                data[6],
                data[7],
                data[8],
                notes,
            )

        twstock.stock.TWSEFetcher._make_datatuple = patched_tws_make_datatuple

        # Also patch TPEXFetcher if it exists (for OTC stocks)
        if hasattr(twstock.stock, "TPEXFetcher"):

            def patched_tpex_make_datatuple(self, data):
                """Convert raw API data to DATATUPLE for TPEX (OTC market)."""
                # Extract notes field if present
                notes = data[9] if len(data) > 9 else ""
                data = data[:9]

                # Convert date format, removing special markers like ＊
                data[0] = datetime.datetime.strptime(
                    self._convert_date(data[0].replace("＊", "")), "%Y/%m/%d"
                )
                # TPEX uses units of 1000 for capacity and turnover
                data[1] = int(data[1].replace(",", "")) * 1000
                data[2] = int(data[2].replace(",", "")) * 1000
                # Convert prices
                data[3] = None if data[3] == "--" else float(data[3].replace(",", ""))
                data[4] = None if data[4] == "--" else float(data[4].replace(",", ""))
                data[5] = None if data[5] == "--" else float(data[5].replace(",", ""))
                data[6] = None if data[6] == "--" else float(data[6].replace(",", ""))
                # Convert change
                data[7] = float(data[7].replace(",", ""))
                # Convert transaction count
                data[8] = int(data[8].replace(",", ""))

                return twstock.stock.DATATUPLE(
                    data[0],
                    data[1],
                    data[2],
                    data[3],
                    data[4],
                    data[5],
                    data[6],
                    data[7],
                    data[8],
                    notes,
                )

            twstock.stock.TPEXFetcher._make_datatuple = patched_tpex_make_datatuple

        twstock.stock._patched_datatuple = True
        logger.debug(
            "Successfully patched twstock library for new API format (10 fields with notes)"
        )


# Apply the patch when this module is imported
_patch_twstock_for_new_api()


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
        end_date: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: int = 2,
    ):
        """
        Initialize Taiwan stock data fetcher.

        Args:
            symbol: Stock ID (e.g., '2330')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), used for filtering
            max_retries: Maximum number of retry attempts
            retry_delay: Base delay between retries in seconds

        Raises:
            ValueError: If date format is invalid
        """
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.max_retries = max_retries
        self.retry_delay = retry_delay

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
        Fetch Taiwan stock data from twstock with retry logic.

        Returns:
            DataFrame with lowercase columns: ['open', 'high', 'low', 'close', 'volume']
            Index: DatetimeIndex named 'date'

        Raises:
            DataFetchError: If download fails after all retries
            DataValidationError: If data is invalid
        """
        logger.info(f"Fetching TW stock data for {self.symbol}")

        for attempt in range(1, self.max_retries + 1):
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
                    logger.warning(
                        f"No data returned for {self.symbol} (attempt {attempt}/{self.max_retries})"
                    )
                    if attempt == self.max_retries:
                        raise DataFetchError(
                            f"No data returned for {self.symbol}",
                            symbol=self.symbol,
                            source="twstock",
                        )
                    continue

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
                    f"from {df.index[0]} to {df.index[-1]} (attempt {attempt}/{self.max_retries})"
                )

                return df

            except (ConnectionError, TimeoutError) as e:
                logger.warning(
                    f"Network error for {self.symbol} (attempt {attempt}/{self.max_retries}): {e}"
                )
                if attempt == self.max_retries:
                    raise DataFetchError(
                        f"Network error fetching {self.symbol}: {e}",
                        symbol=self.symbol,
                        source="twstock",
                    ) from e

            except Exception as e:
                if isinstance(e, (DataFetchError, DataValidationError)):
                    raise
                logger.warning(
                    f"Unexpected error for {self.symbol} (attempt {attempt}/{self.max_retries}): {e}"
                )
                if attempt == self.max_retries:
                    raise DataFetchError(
                        f"Failed to fetch {self.symbol}: {e}", symbol=self.symbol, source="twstock"
                    ) from e

            # Wait before retrying (exponential backoff)
            if attempt < self.max_retries:
                delay = self.retry_delay * (2 ** (attempt - 1))
                logger.debug(f"Retrying {self.symbol} in {delay} seconds...")
                time.sleep(delay)

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
            for idx, symbol in enumerate(symbols, 1):
                try:
                    logger.info(f"[{idx}/{len(symbols)}] Fetching TW stock: {symbol}")

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
