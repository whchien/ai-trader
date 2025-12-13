"""Data fetchers for various markets."""
from ai_trader.data.fetchers.base import (
    BaseFetcher,
    USStockFetcher,
    TWStockFetcher,
    load_example
)
from ai_trader.data.fetchers.crypto import (
    BitcoinDataFetcher,
    CryptoDataFetcher,
    CryptoDataError,
)

__all__ = [
    # Base classes
    "BaseFetcher",

    # Stock fetchers
    "USStockFetcher",
    "TWStockFetcher",

    # Crypto fetchers
    "BitcoinDataFetcher",
    "CryptoDataFetcher",
    "CryptoDataError",

    # Utilities
    "load_example",
]
