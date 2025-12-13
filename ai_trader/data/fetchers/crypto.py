"""
Bitcoin and cryptocurrency data fetcher with retry logic and crypto-specific validation.
"""

import time
from typing import Dict, Optional, Any

import pandas as pd
import numpy as np
import yfinance as yf
from yfinance.exceptions import YFException

from ai_trader.core.logging import get_logger
from ai_trader.core.exceptions import DataFetchError, DataValidationError

logger = get_logger(__name__)


class CryptoDataError(DataValidationError):
    """Cryptocurrency-specific data validation error."""
    pass


class BitcoinDataFetcher:
    """
    Fetches Bitcoin (BTC-USD) market data from Yahoo Finance with retry logic.

    Similar to MarketDataFetcher but specialized for Bitcoin/cryptocurrency data
    with additional validation for crypto-specific characteristics.

    Attributes:
        ticker: Bitcoin ticker symbol (e.g., 'BTC-USD')
        start_date: Start date for data fetch
        end_date: End date for data fetch
        max_retries: Maximum retry attempts on failure
        retry_delay: Base delay between retries (seconds)
        timeout: Request timeout (seconds)

    Example:
        >>> fetcher = BitcoinDataFetcher(
        ...     ticker="BTC-USD",
        ...     start_date="2020-01-01",
        ...     end_date="2024-12-31"
        ... )
        >>> df = fetcher.fetch_bitcoin_data()
        >>> if df is not None:
        ...     metrics = fetcher.calculate_volatility_metrics(df)
        ...     print(f"Volatility: {metrics['annualized_volatility']:.2f}%")
    """

    DEFAULT_TICKER = "BTC-USD"

    def __init__(
        self,
        ticker: str = "BTC-USD",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: int = 2,
        timeout: int = 30
    ):
        """
        Initialize BitcoinDataFetcher.

        Args:
            ticker: Bitcoin ticker symbol (default: 'BTC-USD')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            max_retries: Maximum number of retry attempts
            retry_delay: Base delay between retries in seconds
            timeout: Request timeout in seconds
        """
        self.ticker = ticker
        self.start_date = start_date
        self.end_date = end_date
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout

        logger.info(
            f"Initialized BitcoinDataFetcher for {ticker} "
            f"from {start_date or 'earliest'} to {end_date or 'latest'}"
        )

    def fetch_bitcoin_data(self) -> Optional[pd.DataFrame]:
        """
        Fetch Bitcoin data with retry logic and exponential backoff.

        Returns:
            DataFrame with Bitcoin OHLCV data, or None if fetch fails
            Columns: Date (index), Open, High, Low, Close, Adj Close, Volume

        Raises:
            DataFetchError: If all retry attempts fail

        Example:
            >>> fetcher = BitcoinDataFetcher(start_date="2024-01-01")
            >>> df = fetcher.fetch_bitcoin_data()
            >>> print(f"Fetched {len(df)} rows")
        """
        logger.info(f"Fetching data for {self.ticker}...")

        for attempt in range(1, self.max_retries + 1):
            try:
                # Create ticker object
                ticker_obj = yf.Ticker(self.ticker)

                # Download historical data
                df = ticker_obj.history(
                    start=self.start_date,
                    end=self.end_date,
                    auto_adjust=False,  # Keep both Close and Adj Close
                    actions=False,      # Don't include dividends and splits
                    timeout=self.timeout
                )

                # Validate the data
                if df.empty:
                    logger.warning(f"No data returned for {self.ticker}")
                    if attempt == self.max_retries:
                        raise DataFetchError(
                            f"No data available for {self.ticker}",
                            symbol=self.ticker,
                            source="yfinance"
                        )
                    continue

                # Check if we got the expected columns
                expected_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                missing_columns = [col for col in expected_columns if col not in df.columns]

                if missing_columns:
                    logger.warning(
                        f"Missing columns for {self.ticker}: {missing_columns}"
                    )

                # Log success
                logger.info(
                    f"Successfully fetched {len(df)} rows for {self.ticker} "
                    f"(attempt {attempt}/{self.max_retries})"
                )

                # Ensure the index is named 'Date'
                df.index.name = 'Date'

                return df

            except YFException as e:
                logger.warning(
                    f"Yahoo Finance error for {self.ticker} "
                    f"(attempt {attempt}/{self.max_retries}): {e}"
                )
                if attempt == self.max_retries:
                    raise DataFetchError(
                        f"Failed to fetch {self.ticker} after {self.max_retries} attempts: {e}",
                        symbol=self.ticker,
                        source="yfinance"
                    ) from e

            except Exception as e:
                logger.warning(
                    f"Unexpected error for {self.ticker} "
                    f"(attempt {attempt}/{self.max_retries}): {e}"
                )
                if attempt == self.max_retries:
                    raise DataFetchError(
                        f"Unexpected error fetching {self.ticker}: {e}",
                        symbol=self.ticker,
                        source="yfinance"
                    ) from e

            # Wait before retrying (exponential backoff)
            if attempt < self.max_retries:
                delay = self.retry_delay * (2 ** (attempt - 1))
                logger.debug(f"Retrying {self.ticker} in {delay} seconds...")
                time.sleep(delay)

        # Should not reach here due to exceptions, but just in case
        return None

    def validate_bitcoin_data(
        self,
        df: pd.DataFrame,
        max_daily_change_pct: float = 50.0,
        price_min: float = 100.0,
        price_max: float = 150000.0,
        min_volume: float = 100.0,
        max_gap_days: int = 2
    ) -> bool:
        """
        Validate Bitcoin data for crypto-specific characteristics.

        Performs comprehensive validation including:
        - Price positivity (all prices > 0)
        - Price range within historical bounds
        - Volume consistency (no zero-volume days if required)
        - Daily price changes within volatility thresholds
        - Gap detection for missing trading periods
        - OHLC consistency (Low <= Open/Close <= High)

        Args:
            df: DataFrame with Bitcoin data
            max_daily_change_pct: Maximum allowed daily price change percentage
            price_min: Minimum historical price bound
            price_max: Maximum historical price bound
            min_volume: Minimum volume threshold (millions USD)
            max_gap_days: Maximum allowed gap in trading data

        Returns:
            True if validation passes, False otherwise

        Raises:
            CryptoDataError: If critical validation fails

        Example:
            >>> fetcher = BitcoinDataFetcher()
            >>> df = fetcher.fetch_bitcoin_data()
            >>> is_valid = fetcher.validate_bitcoin_data(df)
            >>> print(f"Data valid: {is_valid}")
        """
        if df.empty:
            logger.error("Cannot validate empty DataFrame")
            raise CryptoDataError(
                "Empty DataFrame provided for validation",
                symbol=self.ticker
            )

        validation_issues = []

        # 1. Check for required columns
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            validation_issues.append(f"Missing required columns: {missing_columns}")

        # 2. Check price positivity
        price_columns = ['Open', 'High', 'Low', 'Close']
        for col in price_columns:
            if col in df.columns:
                negative_prices = (df[col] <= 0).sum()
                if negative_prices > 0:
                    validation_issues.append(
                        f"{col} has {negative_prices} non-positive values"
                    )

        # 3. Check price range bounds
        if 'High' in df.columns:
            max_price = df['High'].max()
            if max_price > price_max:
                validation_issues.append(
                    f"Maximum price {max_price:.2f} exceeds historical bound {price_max:.2f}"
                )

        if 'Low' in df.columns:
            min_price = df['Low'].min()
            if min_price < price_min:
                validation_issues.append(
                    f"Minimum price {min_price:.2f} below historical bound {price_min:.2f}"
                )

        # 4. Check for zero-volume days
        if 'Volume' in df.columns:
            zero_volume_days = (df['Volume'] == 0).sum()
            if zero_volume_days > 0:
                validation_issues.append(
                    f"Found {zero_volume_days} days with zero volume"
                )

        # 5. Check OHLC consistency
        if all(col in df.columns for col in ['Open', 'High', 'Low', 'Close']):
            # High should be >= Open, Close, Low
            high_violations = (
                (df['High'] < df['Open']) |
                (df['High'] < df['Close']) |
                (df['High'] < df['Low'])
            ).sum()

            # Low should be <= Open, Close, High
            low_violations = (
                (df['Low'] > df['Open']) |
                (df['Low'] > df['Close']) |
                (df['Low'] > df['High'])
            ).sum()

            if high_violations > 0:
                validation_issues.append(
                    f"Found {high_violations} High price violations"
                )
            if low_violations > 0:
                validation_issues.append(
                    f"Found {low_violations} Low price violations"
                )

        # 6. Check daily price changes
        if 'Close' in df.columns:
            daily_returns = df['Close'].pct_change() * 100
            extreme_moves = daily_returns[abs(daily_returns) > max_daily_change_pct]

            if len(extreme_moves) > 0:
                validation_issues.append(
                    f"Found {len(extreme_moves)} days with price changes "
                    f"exceeding {max_daily_change_pct}%"
                )
                logger.warning(
                    f"Extreme price movements detected:\n{extreme_moves.describe()}"
                )

        # 7. Check for gaps in data
        date_diff = df.index.to_series().diff()
        gaps = date_diff[date_diff > pd.Timedelta(days=max_gap_days)]
        if len(gaps) > 0:
            validation_issues.append(
                f"Found {len(gaps)} gaps exceeding {max_gap_days} days in data"
            )

        # Log validation results
        if validation_issues:
            logger.warning(f"Validation issues found: {len(validation_issues)}")
            for issue in validation_issues:
                logger.warning(f"  - {issue}")
            return False
        else:
            logger.info("All validation checks passed")
            return True

    def calculate_volatility_metrics(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate Bitcoin-specific volatility metrics.

        Args:
            df: DataFrame with Bitcoin price data

        Returns:
            Dictionary with volatility statistics:
            - daily_volatility: Standard deviation of daily returns (%)
            - annualized_volatility: Annualized volatility (daily_vol * sqrt(365))
            - max_drawdown: Maximum peak-to-trough decline percentage
            - avg_daily_return: Average daily return percentage

        Example:
            >>> fetcher = BitcoinDataFetcher()
            >>> df = fetcher.fetch_bitcoin_data()
            >>> metrics = fetcher.calculate_volatility_metrics(df)
            >>> print(f"Ann. Volatility: {metrics['annualized_volatility']:.2f}%")
            >>> print(f"Max Drawdown: {metrics['max_drawdown']:.2f}%")
        """
        if df.empty or 'Close' not in df.columns:
            logger.warning("Cannot calculate volatility metrics: insufficient data")
            return {}

        # Calculate daily returns
        daily_returns = df['Close'].pct_change().dropna()

        # Daily volatility
        daily_vol = daily_returns.std() * 100  # as percentage

        # Annualized volatility (crypto trades 365 days/year)
        annualized_vol = daily_vol * np.sqrt(365)

        # Average daily return
        avg_daily_return = daily_returns.mean() * 100  # as percentage

        # Calculate max drawdown
        cumulative = (1 + daily_returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min() * 100  # as percentage

        metrics = {
            'daily_volatility': round(daily_vol, 2),
            'annualized_volatility': round(annualized_vol, 2),
            'max_drawdown': round(max_drawdown, 2),
            'avg_daily_return': round(avg_daily_return, 4)
        }

        logger.debug(f"Volatility metrics: {metrics}")
        return metrics

    def get_data_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate comprehensive summary statistics for Bitcoin data.

        Includes crypto-specific metrics:
        - Price range (high/low)
        - Daily returns statistics
        - Volume statistics
        - Trading day count
        - Volatility metrics
        - Total return

        Args:
            df: DataFrame with Bitcoin data

        Returns:
            Dictionary with summary statistics

        Example:
            >>> fetcher = BitcoinDataFetcher()
            >>> df = fetcher.fetch_bitcoin_data()
            >>> summary = fetcher.get_data_summary(df)
            >>> print(f"Total Return: {summary['total_return_pct']:.2f}%")
            >>> print(f"Price Range: ${summary['price_range']['lowest']:.0f} - "
            ...       f"${summary['price_range']['highest']:.0f}")
        """
        if df.empty:
            return {
                "ticker": self.ticker,
                "rows": 0,
                "date_range": None,
                "columns": []
            }

        summary = {
            "ticker": self.ticker,
            "rows": len(df),
            "date_range": {
                "start": df.index.min().strftime("%Y-%m-%d"),
                "end": df.index.max().strftime("%Y-%m-%d")
            },
            "columns": list(df.columns),
            "missing_values": df.isnull().sum().to_dict(),
        }

        # Price statistics
        if all(col in df.columns for col in ['High', 'Low', 'Close']):
            summary["price_range"] = {
                "highest": float(df['High'].max()),
                "lowest": float(df['Low'].min()),
                "latest_close": float(df['Close'].iloc[-1]),
                "first_close": float(df['Close'].iloc[0])
            }

            # Calculate total return
            total_return = (
                (df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]
            ) * 100
            summary["total_return_pct"] = round(total_return, 2)

        # Volume statistics
        if 'Volume' in df.columns:
            summary["volume"] = {
                "mean": float(df['Volume'].mean()),
                "median": float(df['Volume'].median()),
                "max": float(df['Volume'].max())
            }

        # Volatility metrics
        volatility_metrics = self.calculate_volatility_metrics(df)
        if volatility_metrics:
            summary["volatility"] = volatility_metrics

        return summary


class CryptoDataFetcher(BitcoinDataFetcher):
    """
    Generic cryptocurrency data fetcher supporting multiple crypto assets.

    Extends BitcoinDataFetcher to support any cryptocurrency available on Yahoo Finance.

    Supported tickers include:
    - BTC-USD (Bitcoin)
    - ETH-USD (Ethereum)
    - BNB-USD (Binance Coin)
    - ADA-USD (Cardano)
    - SOL-USD (Solana)
    - And many more...

    Example:
        >>> # Fetch Ethereum data
        >>> eth_fetcher = CryptoDataFetcher(
        ...     ticker="ETH-USD",
        ...     start_date="2023-01-01"
        ... )
        >>> eth_data = eth_fetcher.fetch_bitcoin_data()  # Works for any crypto
        >>>
        >>> # Fetch Solana data
        >>> sol_fetcher = CryptoDataFetcher(ticker="SOL-USD")
        >>> sol_data = sol_fetcher.fetch_bitcoin_data()
    """

    def __init__(self, ticker: str, **kwargs):
        """
        Initialize CryptoDataFetcher for any cryptocurrency.

        Args:
            ticker: Cryptocurrency ticker (e.g., 'ETH-USD', 'SOL-USD')
            **kwargs: Additional arguments passed to BitcoinDataFetcher

        Example:
            >>> fetcher = CryptoDataFetcher(
            ...     ticker="ETH-USD",
            ...     start_date="2024-01-01",
            ...     max_retries=5
            ... )
        """
        super().__init__(ticker=ticker, **kwargs)
        logger.info(f"Initialized CryptoDataFetcher for {ticker}")


if __name__ == "__main__":
    # Example usage
    fetcher = BitcoinDataFetcher(start_date="2024-01-01", end_date="2024-12-31")
    df = fetcher.fetch_bitcoin_data()

    if df is not None:
        print(f"\nFetched {len(df)} rows of Bitcoin data")
        print(f"\nData Summary:")
        summary = fetcher.get_data_summary(df)
        print(f"Date Range: {summary['date_range']['start']} to {summary['date_range']['end']}")
        print(f"Price Range: ${summary['price_range']['lowest']:.2f} - ${summary['price_range']['highest']:.2f}")
        print(f"Total Return: {summary['total_return_pct']:.2f}%")
        print(f"\nVolatility Metrics:")
        print(f"  Daily Volatility: {summary['volatility']['daily_volatility']:.2f}%")
        print(f"  Annualized Volatility: {summary['volatility']['annualized_volatility']:.2f}%")
        print(f"  Max Drawdown: {summary['volatility']['max_drawdown']:.2f}%")

        # Validate the data
        is_valid = fetcher.validate_bitcoin_data(df)
        print(f"\nData Validation: {'PASSED' if is_valid else 'FAILED'}")
