"""Data fetchers for various markets."""
from ai_trader.data.fetchers.base import (
    BaseFetcher,
    load_example
)
from ai_trader.data.fetchers.vix import VIXDataFetcher
from ai_trader.data.fetchers.forex import ForexDataFetcher
from ai_trader.data.fetchers.tw_stock import TWStockFetcher
from ai_trader.data.fetchers.us_stock import USStockFetcher
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
