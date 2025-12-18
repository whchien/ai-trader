"""
File management for market data CSV operations.
"""

from pathlib import Path
from typing import Optional

import pandas as pd

from ai_trader.core.logging import get_logger


class FileManager:
    """
    Manages file operations for market data CSV files.
    """

    def __init__(self, base_data_dir: str = "data"):
        """
        Initialize FileManager.

        Args:
            base_data_dir: Base directory for storing data files
        """
        self.base_data_dir = Path(base_data_dir)
        self.logger = get_logger(__name__)
        self.ensure_directory_exists(self.base_data_dir)

    def ensure_directory_exists(self, path: Path):
        """
        Create directory if it doesn't exist.

        Args:
            path: Directory path to create
        """
        path.mkdir(parents=True, exist_ok=True)
        self.logger.debug(f"Ensured directory exists: {path}")

    def generate_filename(self, ticker: str, start_date: str, end_date: str) -> str:
        """
        Generate standardized filename for market data.

        Special characters like ^ are replaced for filesystem compatibility:
        - ^ is replaced with INDEX_

        Args:
            ticker: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Formatted filename

        Example:
            ^GSPC -> INDEX_GSPC_2000-01-01_to_2025-12-31.csv
        """
        # Replace special characters for filesystem compatibility
        safe_ticker = ticker.replace("^", "INDEX_")

        filename = f"{safe_ticker}_{start_date}_to_{end_date}.csv"
        return filename

    def save_to_csv(
        self, df: pd.DataFrame, ticker: str, start_date: str, end_date: str, overwrite: bool = True
    ) -> str:
        """
        Save DataFrame to CSV file.

        Expected DataFrame format:
        - Index: DatetimeIndex with dates (will be saved as first column)
        - Columns: lowercase OHLCV columns ['open', 'high', 'low', 'close', 'volume']
        - Optional additional columns (e.g., 'adj_close') are allowed

        Args:
            df: DataFrame containing market data
            ticker: Stock ticker symbol
            start_date: Start date of data (YYYY-MM-DD)
            end_date: End date of data (YYYY-MM-DD)
            overwrite: Whether to overwrite existing file

        Returns:
            Path to saved file

        Raises:
            ValueError: If DataFrame is empty
            IOError: If file write fails
        """
        if df.empty:
            raise ValueError(f"Cannot save empty DataFrame for ticker {ticker}")

        filename = self.generate_filename(ticker, start_date, end_date)
        filepath = self.base_data_dir / filename

        # Check if file exists and overwrite flag
        if filepath.exists() and not overwrite:
            self.logger.warning(f"File already exists and overwrite=False: {filepath}")
            return str(filepath)

        try:
            # Save to CSV with index (Date column)
            df.to_csv(filepath, index=True)
            file_size = filepath.stat().st_size
            self.logger.info(
                f"Saved {ticker} data to {filepath} ({len(df)} rows, {file_size:,} bytes)"
            )
            return str(filepath)

        except Exception as e:
            self.logger.error(f"Failed to save {ticker} data to {filepath}: {e}")
            raise OSError(f"Failed to write file {filepath}: {e}") from e

    def load_from_csv(self, filepath: str, parse_dates: bool = True) -> pd.DataFrame:
        """
        Load market data from CSV file.

        Args:
            filepath: Path to CSV file
            parse_dates: Whether to parse date column

        Returns:
            DataFrame containing market data

        Raises:
            FileNotFoundError: If file doesn't exist
            pd.errors.EmptyDataError: If file is empty
        """
        file_path = Path(filepath)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        try:
            df = pd.read_csv(
                filepath, index_col=0, parse_dates=parse_dates if parse_dates else False
            )
            self.logger.info(f"Loaded {len(df)} rows from {filepath}")
            return df

        except Exception as e:
            self.logger.error(f"Failed to load data from {filepath}: {e}")
            raise

    def get_existing_data_files(self, ticker: Optional[str] = None) -> list[str]:
        """
        List existing data files in the data directory.

        Args:
            ticker: Optional ticker to filter by (e.g., "^GSPC")

        Returns:
            List of file paths
        """
        if not self.base_data_dir.exists():
            return []

        csv_files = list(self.base_data_dir.glob("*.csv"))

        if ticker:
            # Convert ticker to safe filename format for matching
            safe_ticker = ticker.replace("^", "INDEX_")
            csv_files = [f for f in csv_files if safe_ticker in f.name]

        return [str(f) for f in csv_files]

    def file_exists(self, ticker: str, start_date: str, end_date: str) -> bool:
        """
        Check if a data file already exists.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            True if file exists, False otherwise
        """
        filename = self.generate_filename(ticker, start_date, end_date)
        filepath = self.base_data_dir / filename
        return filepath.exists()

    def delete_file(self, ticker: str, start_date: str, end_date: str) -> bool:
        """
        Delete a data file.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            True if deleted, False if file didn't exist
        """
        filename = self.generate_filename(ticker, start_date, end_date)
        filepath = self.base_data_dir / filename

        if filepath.exists():
            filepath.unlink()
            self.logger.info(f"Deleted file: {filepath}")
            return True
        else:
            self.logger.warning(f"File not found for deletion: {filepath}")
            return False

    def get_data_directory_info(self) -> dict:
        """
        Get information about the data directory.

        Returns:
            Dictionary with directory statistics
        """
        if not self.base_data_dir.exists():
            return {"exists": False, "file_count": 0, "total_size": 0}

        csv_files = list(self.base_data_dir.glob("*.csv"))
        total_size = sum(f.stat().st_size for f in csv_files)

        return {
            "exists": True,
            "file_count": len(csv_files),
            "total_size": total_size,
            "files": [f.name for f in csv_files],
        }
