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

    def __init__(self, symbol: str, start_date: str, end_date: Optional[str] = None):
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
                auto_adjust=False,  # Keep both Close and Adj Close
            )

            if df.empty:
                raise DataFetchError(
                    f"No data returned for {self.symbol}", symbol=self.symbol, source="yfinance"
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
                f"Network error fetching {self.symbol}: {e}", symbol=self.symbol, source="yfinance"
            ) from e
        except Exception as e:
            if isinstance(e, (DataFetchError, DataValidationError)):
                raise
            raise DataFetchError(
                f"Failed to fetch {self.symbol}: {e}", symbol=self.symbol, source="yfinance"
            ) from e

    def fetch_batch(self, symbols: list[str]) -> tuple[dict[str, pd.DataFrame], list[str]]:
        """
        Fetch data for multiple US stocks efficiently.

        Uses yfinance's multi-ticker download to fetch all symbols in a single API call,
        which is much faster than individual requests.

        Args:
            symbols: List of stock ticker symbols (e.g., ['AAPL', 'MSFT', 'GOOGL'])

        Returns:
            Tuple of (successful_data, failed_symbols):
            - successful_data: Dict mapping symbol -> DataFrame with OHLCV data
            - failed_symbols: List of symbols that failed to download

        Example:
            >>> fetcher = USStockFetcher(symbol="", start_date="2020-01-01")
            >>> data, failed = fetcher.fetch_batch(['AAPL', 'MSFT'])
            >>> print(f"Downloaded {len(data)} stocks, {len(failed)} failed")
        """
        if not symbols:
            logger.warning("fetch_batch called with empty symbol list")
            return {}, []

        logger.info(f"Fetching batch of {len(symbols)} US stocks: {symbols}")

        successful_data = {}
        failed_symbols = []

        try:
            # Download all symbols in one API call (space-separated)
            symbols_str = " ".join(symbols)
            logger.debug(f"Downloading: {symbols_str}")

            df = yf.download(
                symbols_str,
                start=self.start_date,
                end=self.end_date,
                progress=False,
                auto_adjust=False,
                group_by="ticker",  # Group by ticker for easier splitting
            )

            if df.empty:
                logger.warning("yfinance returned empty DataFrame for all symbols")
                failed_symbols = symbols.copy()
                return {}, failed_symbols

            # Handle single vs multiple symbols
            if len(symbols) == 1:
                # Single symbol: df has simple columns (Open, High, Low, ...)
                symbol = symbols[0]
                try:
                    df_copy = df.reset_index()
                    df_normalized = self._normalize_columns(df_copy)
                    self._validate_dataframe(df_normalized, symbol)
                    successful_data[symbol] = df_normalized
                    logger.info(f"Successfully fetched {symbol}: {len(df_normalized)} rows")
                except Exception as e:
                    logger.warning(f"Failed to process {symbol}: {e}")
                    failed_symbols.append(symbol)
            else:
                # Multiple symbols: df has MultiIndex columns (symbol, column_name)
                for symbol in symbols:
                    try:
                        # Extract data for this symbol
                        if symbol in df.columns.get_level_values(0):
                            symbol_df = df[symbol].copy()
                            symbol_df = symbol_df.reset_index()

                            # Normalize and validate
                            symbol_df = self._normalize_columns(symbol_df)

                            # Check for all-NaN data (invalid symbols)
                            if symbol_df[["open", "high", "low", "close"]].isna().all().all():
                                logger.warning(f"Symbol {symbol} has no valid data (all NaN)")
                                failed_symbols.append(symbol)
                                continue

                            self._validate_dataframe(symbol_df, symbol)

                            successful_data[symbol] = symbol_df
                            logger.info(
                                f"Successfully fetched {symbol}: {len(symbol_df)} rows "
                                f"from {symbol_df.index[0]} to {symbol_df.index[-1]}"
                            )
                        else:
                            logger.warning(f"Symbol {symbol} not found in downloaded data")
                            failed_symbols.append(symbol)
                    except Exception as e:
                        logger.warning(f"Failed to process {symbol}: {e}")
                        failed_symbols.append(symbol)

        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Network error during batch fetch: {e}")
            failed_symbols = symbols.copy()
        except Exception as e:
            logger.error(f"Unexpected error during batch fetch: {e}")
            failed_symbols = symbols.copy()

        logger.info(
            f"Batch fetch complete: {len(successful_data)} succeeded, {len(failed_symbols)} failed"
        )

        return successful_data, failed_symbols
