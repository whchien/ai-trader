import re
from typing import List


def check_rules(conds: List[bool], cutoff: int) -> bool:
    return sum(1 for cond in conds if not cond) >= cutoff


def extract_ticker_from_path(file_path: str) -> str:
    """
    Extracts the ticker symbol from the given file path.
    """
    match = re.search(r"/([^/]+)\.csv$", file_path)
    if match:
        return match.group(1)
    else:
        raise ValueError("Ticker symbol not found in the file path")
