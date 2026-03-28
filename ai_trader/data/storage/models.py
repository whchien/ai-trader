"""SQLModel table definitions for market data storage."""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class USStockData(SQLModel, table=True):
    """US stock market data with adjusted close."""

    __tablename__ = "us_stock_data"

    id: Optional[int] = Field(default=None, primary_key=True)
    ticker: str
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float
    adj_close: Optional[float] = None


class TWStockData(SQLModel, table=True):
    """Taiwan stock market data (no adjusted close)."""

    __tablename__ = "tw_stock_data"

    id: Optional[int] = Field(default=None, primary_key=True)
    ticker: str
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float


class CryptoData(SQLModel, table=True):
    """Cryptocurrency market data."""

    __tablename__ = "crypto_data"

    id: Optional[int] = Field(default=None, primary_key=True)
    ticker: str
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float
    adj_close: Optional[float] = None


class ForexData(SQLModel, table=True):
    """Forex market data (volume always 0)."""

    __tablename__ = "forex_data"

    id: Optional[int] = Field(default=None, primary_key=True)
    ticker: str
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float
    adj_close: Optional[float] = None


class VIXData(SQLModel, table=True):
    """VIX index data."""

    __tablename__ = "vix_data"

    id: Optional[int] = Field(default=None, primary_key=True)
    ticker: str
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float
    adj_close: Optional[float] = None


class DataMetadata(SQLModel, table=True):
    """Metadata to track data coverage per ticker/market."""

    __tablename__ = "data_metadata"

    id: Optional[int] = Field(default=None, primary_key=True)
    ticker: str
    market_type: str
    first_date: date
    last_date: date
    total_rows: int
    last_fetched_at: datetime
