"""Data fetchers for various markets."""
from ai_trader.data.fetchers.base import (
    BaseFetcher,
    USStockFetcher,
    TWStockFetcher,
    ForexDataFetcher,
    VIXDataFetcher,
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

    # Forex and indices
    "ForexDataFetcher",
    "VIXDataFetcher",

    # Crypto fetchers
    "BitcoinDataFetcher",
    "CryptoDataFetcher",
    "CryptoDataError",

    # Utilities
    "load_example",
]
