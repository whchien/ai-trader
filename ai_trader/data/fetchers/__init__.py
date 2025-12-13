"""Data fetchers for various markets."""
from ai_trader.data.fetchers.base import BaseFetcher, MarketDataFetcher, load_example
from ai_trader.data.fetchers.crypto import (
    BitcoinDataFetcher,
    CryptoDataFetcher,
    CryptoDataError,
)

__all__ = [
    "BaseFetcher",
    "MarketDataFetcher",
    "BitcoinDataFetcher",
    "CryptoDataFetcher",
    "CryptoDataError",
    "load_example",
]
