"""SQLite storage implementation using SQLModel ORM."""

from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
from sqlalchemy import select
from sqlmodel import Session, create_engine

from ai_trader.core.logging import get_logger

from sqlmodel import SQLModel

from .models import (
    CryptoData,
    DataMetadata,
    ForexData,
    TWStockData,
    USStockData,
    VIXData,
)

logger = get_logger(__name__)

# Market type -> SQLModel class mapping
MARKET_MODEL_MAP = {
    "us_stock": USStockData,
    "tw_stock": TWStockData,
    "crypto": CryptoData,
    "forex": ForexData,
    "vix": VIXData,
}


class SQLiteDataStorage:
    """Manage market data persistence with SQLite and SQLModel ORM."""

    def __init__(self, db_path: str = "data/market_data.db"):
        """
        Initialize SQLite storage.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # SQLite URL
        db_url = f"sqlite:///{self.db_path.resolve()}"
        self.engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            echo=False,
        )

        # Create all tables
        SQLModel.metadata.create_all(self.engine)
        logger.info(f"Initialized SQLite storage at {self.db_path}")

    def get_coverage(self, ticker: str, market_type: str) -> Optional[tuple[date, date]]:
        """
        Get date range coverage for a ticker in a market.

        Args:
            ticker: Stock ticker symbol
            market_type: Market type (us_stock, tw_stock, crypto, forex, vix)

        Returns:
            Tuple of (first_date, last_date), or None if no data
        """
        with Session(self.engine) as session:
            meta = session.exec(
                select(DataMetadata)
                .where(DataMetadata.ticker == ticker)
                .where(DataMetadata.market_type == market_type)
            ).unique().scalars().first()

            if meta:
                # Access attributes before session closes
                first = meta.first_date
                last = meta.last_date
                return first, last
            return None

    def load(
        self, ticker: str, market_type: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """
        Load market data from database as DataFrame.

        Args:
            ticker: Stock ticker symbol
            market_type: Market type
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with OHLCV data, indexed by date
        """
        model = MARKET_MODEL_MAP[market_type]
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)

        with Session(self.engine) as session:
            rows = session.exec(
                select(model)
                .where(model.ticker == ticker)
                .where(model.date >= start)
                .where(model.date <= end)
                .order_by(model.date)
            ).unique().scalars().all()

        if not rows:
            logger.warning(f"No data found for {ticker} in {market_type}")
            return pd.DataFrame()

        df = self._rows_to_dataframe(rows, market_type)
        logger.info(f"Loaded {len(df)} rows for {ticker} from {market_type} table")
        return df

    def save(self, df: pd.DataFrame, ticker: str, market_type: str) -> int:
        """
        Upsert market data into database using ORM.

        Args:
            df: DataFrame with OHLCV data (index: date)
            ticker: Stock ticker symbol
            market_type: Market type

        Returns:
            Number of rows inserted/updated

        Raises:
            ValueError: If DataFrame is empty or market_type is invalid
        """
        if df.empty:
            raise ValueError(f"Cannot save empty DataFrame for {ticker}")

        if market_type not in MARKET_MODEL_MAP:
            raise ValueError(f"Invalid market_type: {market_type}")

        model = MARKET_MODEL_MAP[market_type]

        # Convert DataFrame rows to model instances
        rows = self._dataframe_to_rows(df, ticker, model)

        # Upsert using ORM (session.merge handles INSERT OR REPLACE)
        with Session(self.engine) as session:
            for row in rows:
                session.merge(row)
            session.commit()

        # Update metadata
        self._update_metadata(ticker, market_type, df)

        logger.info(f"Saved {len(rows)} rows for {ticker} to {market_type} table")
        return len(rows)

    def get_missing_ranges(
        self, ticker: str, market_type: str, target_start: str, target_end: str
    ) -> list[tuple[str, str]]:
        """
        Calculate date ranges that are NOT in the database.

        Args:
            ticker: Stock ticker symbol
            market_type: Market type
            target_start: Desired start date (YYYY-MM-DD)
            target_end: Desired end date (YYYY-MM-DD)

        Returns:
            List of (start, end) date ranges to fetch.
            Empty list if all dates are cached.
            [(target_start, target_end)] if nothing is cached.
        """
        coverage = self.get_coverage(ticker, market_type)
        if not coverage:
            return [(target_start, target_end)]

        db_start, db_end = coverage
        t_start = date.fromisoformat(target_start)
        t_end = date.fromisoformat(target_end)
        missing = []

        # Before existing data
        if t_start < db_start:
            missing.append((target_start, (db_start - timedelta(days=1)).isoformat()))

        # After existing data
        if t_end > db_end:
            missing.append(((db_end + timedelta(days=1)).isoformat(), target_end))

        return missing

    def delete_ticker(self, ticker: str, market_type: str) -> int:
        """
        Delete all data for a ticker.

        Args:
            ticker: Stock ticker symbol
            market_type: Market type

        Returns:
            Number of rows deleted
        """
        model = MARKET_MODEL_MAP[market_type]

        with Session(self.engine) as session:
            # Delete rows
            stmt = select(model).where(model.ticker == ticker)
            rows = session.exec(stmt).unique().scalars().all()
            count = len(rows)

            for row in rows:
                session.delete(row)

            # Delete metadata
            meta_stmt = (
                select(DataMetadata)
                .where(DataMetadata.ticker == ticker)
                .where(DataMetadata.market_type == market_type)
            )
            meta = session.exec(meta_stmt).unique().scalars().first()
            if meta:
                session.delete(meta)

            session.commit()

        logger.info(f"Deleted {count} rows for {ticker} from {market_type}")
        return count

    def delete_before(self, market_type: str, before_date: str) -> int:
        """
        Delete all data before a given date in a market.

        Args:
            market_type: Market type
            before_date: Delete rows before this date (YYYY-MM-DD)

        Returns:
            Number of rows deleted
        """
        model = MARKET_MODEL_MAP[market_type]
        cutoff = date.fromisoformat(before_date)

        with Session(self.engine) as session:
            stmt = select(model).where(model.date < cutoff)
            rows = session.exec(stmt).unique().scalars().all()
            count = len(rows)

            for row in rows:
                session.delete(row)

            session.commit()

        logger.info(f"Deleted {count} rows before {before_date} from {market_type}")
        return count

    def list_tickers(self, market_type: Optional[str] = None) -> list[dict]:
        """
        List all tickers and their metadata.

        Args:
            market_type: Filter by market type (optional)

        Returns:
            List of dicts with ticker, market, from, to, rows
        """
        with Session(self.engine) as session:
            query = select(DataMetadata)
            if market_type:
                query = query.where(DataMetadata.market_type == market_type)

            metas = session.exec(query).unique().scalars().all()

        return [
            {
                "ticker": m.ticker,
                "market": m.market_type,
                "from": m.first_date.isoformat(),
                "to": m.last_date.isoformat(),
                "rows": m.total_rows,
            }
            for m in metas
        ]

    def get_database_info(self) -> dict:
        """
        Get database statistics.

        Returns:
            Dict with file size, table counts, etc.
        """
        info = {"path": str(self.db_path.resolve())}

        if self.db_path.exists():
            info["exists"] = True
            info["size_bytes"] = self.db_path.stat().st_size
        else:
            info["exists"] = False
            info["size_bytes"] = 0

        with Session(self.engine) as session:
            # Count metadata entries by market
            counts = {}
            for market_type in MARKET_MODEL_MAP.keys():
                count = session.exec(
                    select(DataMetadata).where(DataMetadata.market_type == market_type)
                ).all()
                counts[market_type] = len(count)

            info["tickers_by_market"] = counts
            info["total_tickers"] = sum(counts.values())

        return info

    # ── Private helpers ──────────────────────────────────────────────────────

    def _dataframe_to_rows(self, df: pd.DataFrame, ticker: str, model_class):
        """Convert DataFrame to SQLModel row instances."""
        rows = []
        for dt, row in df.iterrows():
            # Normalize column names
            data = {
                "ticker": ticker,
                "date": dt.date() if hasattr(dt, "date") else dt,
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
            }

            # Handle adj_close if the column exists (normalize "adj close" -> "adj_close")
            adj_close_col = None
            if "adj_close" in row.index:
                adj_close_col = "adj_close"
            elif "adj close" in row.index:
                adj_close_col = "adj close"

            if adj_close_col and hasattr(model_class, "adj_close"):
                val = row[adj_close_col]
                if pd.notna(val):
                    data["adj_close"] = float(val)

            rows.append(model_class(**data))

        return rows

    def _rows_to_dataframe(self, rows: list, market_type: str) -> pd.DataFrame:
        """Convert SQLModel rows to DataFrame."""
        if not rows:
            return pd.DataFrame()

        data = []
        for row in rows:
            row_dict = {
                "open": row.open,
                "high": row.high,
                "low": row.low,
                "close": row.close,
                "volume": row.volume,
            }

            # Add adj_close if it exists on the row
            if hasattr(row, "adj_close") and row.adj_close is not None:
                row_dict["adj_close"] = row.adj_close

            data.append(row_dict)

        df = pd.DataFrame(data)

        # Set date index from the first row's date (all rows should have same ticker)
        if rows:
            df.index = pd.DatetimeIndex([row.date for row in rows], name="date")

        return df

    def _update_metadata(self, ticker: str, market_type: str, df: pd.DataFrame) -> None:
        """Update or create metadata entry."""
        if df.empty:
            return

        first_date = df.index.min().date() if hasattr(df.index.min(), "date") else df.index.min()
        last_date = df.index.max().date() if hasattr(df.index.max(), "date") else df.index.max()

        with Session(self.engine) as session:
            # Try to find existing metadata
            stmt = (
                select(DataMetadata)
                .where(DataMetadata.ticker == ticker)
                .where(DataMetadata.market_type == market_type)
            )
            meta = session.exec(stmt).unique().scalars().first()

            if meta:
                # Update existing
                meta.first_date = min(meta.first_date, first_date)
                meta.last_date = max(meta.last_date, last_date)
                meta.total_rows = len(df)
                meta.last_fetched_at = datetime.now()
                session.add(meta)
            else:
                # Create new
                meta = DataMetadata(
                    ticker=ticker,
                    market_type=market_type,
                    first_date=first_date,
                    last_date=last_date,
                    total_rows=len(df),
                    last_fetched_at=datetime.now(),
                )
                session.add(meta)

            session.commit()
