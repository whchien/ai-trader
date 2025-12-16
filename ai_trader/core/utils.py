"""Utility functions for ai-trader."""

import re
from typing import List

from ai_trader.core.logging import get_logger

logger = get_logger(__name__)


def check_rules(conds: List[bool], cutoff: int) -> bool:
    """
    Check if the number of failed conditions meets or exceeds the cutoff.

    Args:
        conds: List of boolean conditions
        cutoff: Minimum number of False conditions required

    Returns:
        True if number of False conditions >= cutoff, False otherwise

    Example:
        >>> check_rules([True, False, False, True], cutoff=2)
        True
    """
    return sum(1 for cond in conds if not cond) >= cutoff


def extract_ticker_from_path(file_path: str) -> str:
    """
    Extract the ticker symbol from the given file path.

    Args:
        file_path: Path to CSV file (e.g., "data/AAPL.csv" or "data/2330.csv")

    Returns:
        Ticker symbol extracted from filename

    Raises:
        ValueError: If ticker symbol cannot be extracted

    Example:
        >>> extract_ticker_from_path("data/us_stock/AAPL.csv")
        'AAPL'
        >>> extract_ticker_from_path("data/tw_stock/2330.csv")
        '2330'
    """
    match = re.search(r"/([^/]+)\.csv$", file_path)
    if match:
        return match.group(1)
    else:
        raise ValueError("Ticker symbol not found in the file path")
