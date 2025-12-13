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
    def fetch(self, symbol: str, start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Fetch market data for a single symbol.

        Args:
            symbol: Stock symbol/ticker
            start_date: Start date for data
            end_date: Optional end date

        Returns:
            DataFrame with OHLCV data

        Raises:
            DataFetchError: If fetching fails
            DataValidationError: If data is invalid
        """
        pass


class MarketDataFetcher(BaseFetcher):
    """
    Fetches market data from yfinance (US) or twstock (TW).

    This class downloads stock market data and saves it to CSV files.
    Supports both US and Taiwan markets.

    Attributes:
        stocks: List of stock symbols to fetch
        market: Market type ('us' or 'tw')
        start_ym: Start year and month as tuple (year, month)
        save_dir: Directory to save CSV files

    Example:
        >>> fetcher = MarketDataFetcher(
        ...     stocks=["AAPL", "MSFT"],
        ...     market="us",
        ...     start_ym=(2020, 1),
        ...     save_dir="./data/us_stock/"
        ... )
        >>> fetcher.run()
    """

    def __init__(
        self,
        stocks: List[str],
        market: Literal["us", "tw"] = "tw",
        start_ym: Tuple[int, int] = (2024, 1),
        save_dir: str = "./data/tw_stock/",
    ):
        if market not in ["us", "tw"]:
            raise ConfigurationError(
                f"Invalid market '{market}'. Must be 'us' or 'tw'",
                field="market"
            )

        self.stocks = stocks
        self.market = market
        self.start_ym = start_ym
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"Initialized MarketDataFetcher: market={market}, "
            f"stocks={len(stocks)}, start={start_ym}"
        )

    def fetch(self, symbol: str, start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Fetch data for a single symbol.

        Args:
            symbol: Stock symbol
            start_date: Start date (YYYY-MM-DD format)
            end_date: Optional end date

        Returns:
            DataFrame with OHLCV data

        Raises:
            DataFetchError: If fetching fails
            DataValidationError: If data is invalid
        """
        logger.info(f"Fetching data for {symbol} from {start_date}")

        try:
            if self.market == "us":
                df = yf.download(symbol, start=start_date, end=end_date, progress=False)
                df = df.reset_index()
            elif self.market == "tw":
                year, month = self.start_ym
                stock = Stock(symbol)
                stock.fetch_from(year=year, month=month)

                if not stock.data:
                    raise DataFetchError(
                        f"No data returned for {symbol}",
                        symbol=symbol,
                        source="twstock"
                    )

                data_dicts = [d._asdict() for d in stock.data]
                df = pd.DataFrame(data_dicts)
                df = df[["date", "open", "high", "low", "close", "capacity"]]
                df = df.rename({"capacity": "volume"}, axis=1)
            else:
                raise ConfigurationError(
                    f"Invalid market: {self.market}",
                    field="market"
                )

            # Validate the data
            self._validate_dataframe(df, symbol)
            return df

        except (ConnectionError, TimeoutError) as e:
            raise DataFetchError(
                f"Network error fetching {symbol}: {e}",
                symbol=symbol,
                source=self.market
            ) from e
        except Exception as e:
            if isinstance(e, (DataFetchError, DataValidationError, ConfigurationError)):
                raise
            raise DataFetchError(
                f"Failed to fetch {symbol}: {e}",
                symbol=symbol,
                source=self.market
            ) from e

    def _validate_dataframe(self, df: pd.DataFrame, symbol: str) -> None:
        """
        Validate that the DataFrame has required columns and data.

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

        # Check for required columns (case-insensitive)
        df_cols_lower = [col.lower() for col in df.columns]
        required = ["open", "high", "low", "close", "volume"]
        missing = [col for col in required if col not in df_cols_lower]

        if missing:
            raise DataValidationError(
                f"Missing required columns for {symbol}: {missing}",
                symbol=symbol,
                issues=missing
            )

        logger.debug(f"Validated data for {symbol}: {len(df)} rows")

    def save_one_stock_to_csv(self, stock_id: str) -> None:
        """
        Fetch and save data for a single stock.

        Args:
            stock_id: Stock symbol/ID

        Raises:
            DataFetchError: If fetching fails
        """
        logger.info(f"Processing: {stock_id}")

        try:
            start_date = f"{self.start_ym[0]:04d}-{self.start_ym[1]:02d}-01"
            df = self.fetch(stock_id, start_date)

            filepath = self.save_dir / f"{stock_id}.csv"
            df.to_csv(filepath, index=False)
            logger.info(f"Saved: {filepath}")

        except (DataFetchError, DataValidationError) as e:
            logger.error(f"Failed to process {stock_id}: {e}")
            raise

    def run(self) -> None:
        """
        Fetch and save data for all stocks concurrently.

        Uses ThreadPoolExecutor for parallel downloads.
        """
        logger.info(f"Starting data fetch for {len(self.stocks)} stocks")

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self.save_one_stock_to_csv, stock_id): stock_id
                for stock_id in self.stocks
            }

            completed = 0
            failed = 0

            for future in concurrent.futures.as_completed(futures):
                stock_id = futures[future]
                try:
                    future.result()
                    completed += 1
                except Exception as e:
                    logger.error(f"Error fetching {stock_id}: {e}")
                    failed += 1

        logger.info(
            f"Finished: {completed} succeeded, {failed} failed "
            f"out of {len(self.stocks)} total"
        )


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

    date_col = "date" if market == "tw" else "Date"
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


if __name__ == "__main__":
    # Example usage
    fetcher = MarketDataFetcher(
        stocks=["2330"],
        market="tw",
        start_ym=(2019, 1),
        save_dir="./data/tw_stock/"
    )
    fetcher.run()
