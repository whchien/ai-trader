"""Tests for utility functions."""
import pytest
from pathlib import Path
from ai_trader.utils import check_rules, extract_ticker_from_path


class TestCheckRules:
    """Test check_rules function."""

    def test_check_rules_all_true(self):
        """Test check_rules when all conditions are True."""
        conds = [True, True, True, True]
        assert check_rules(conds, cutoff=2) is False  # Not enough False

    def test_check_rules_all_false(self):
        """Test check_rules when all conditions are False."""
        conds = [False, False, False, False]
        assert check_rules(conds, cutoff=2) is True  # More than cutoff False

    def test_check_rules_at_cutoff(self):
        """Test check_rules when exactly at cutoff."""
        conds = [True, True, False, False]
        assert check_rules(conds, cutoff=2) is True  # Exactly cutoff False

    def test_check_rules_below_cutoff(self):
        """Test check_rules when below cutoff."""
        conds = [True, True, True, False]
        assert check_rules(conds, cutoff=2) is False  # Only 1 False

    def test_check_rules_above_cutoff(self):
        """Test check_rules when above cutoff."""
        conds = [False, False, False, True]
        assert check_rules(conds, cutoff=2) is True  # 3 False > cutoff

    def test_check_rules_empty_list(self):
        """Test check_rules with empty list."""
        conds = []
        assert check_rules(conds, cutoff=2) is False  # 0 False < cutoff

    def test_check_rules_single_element(self):
        """Test check_rules with single element."""
        assert check_rules([False], cutoff=1) is True
        assert check_rules([True], cutoff=1) is False

    def test_check_rules_zero_cutoff(self):
        """Test check_rules with zero cutoff."""
        conds = [False, False]
        assert check_rules(conds, cutoff=0) is True  # Any False > 0


class TestExtractTickerFromPath:
    """Test extract_ticker_from_path function."""

    def test_extract_ticker_simple(self):
        """Test extracting ticker from simple filename."""
        path = "data/AAPL.csv"
        ticker = extract_ticker_from_path(path)
        assert ticker == "AAPL"

    def test_extract_ticker_with_directory(self):
        """Test extracting ticker from path with directories."""
        path = "./data/us_stock/TSLA.csv"
        ticker = extract_ticker_from_path(path)
        assert ticker == "TSLA"

    def test_extract_ticker_absolute_path(self):
        """Test extracting ticker from absolute path."""
        path = "/Users/test/data/MSFT.csv"
        ticker = extract_ticker_from_path(path)
        assert ticker == "MSFT"

    def test_extract_ticker_taiwan_stock(self):
        """Test extracting ticker from Taiwan stock file."""
        path = "data/tw_stock/2330.csv"
        ticker = extract_ticker_from_path(path)
        assert ticker == "2330"

    def test_extract_ticker_no_extension(self):
        """Test extracting ticker from file without extension."""
        path = "data/GOOGL"
        # Should still extract the filename
        ticker = extract_ticker_from_path(path)
        assert ticker == "GOOGL"

    def test_extract_ticker_pathlib_path(self):
        """Test extracting ticker from pathlib.Path object."""
        path = Path("data/AMZN.csv")
        ticker = extract_ticker_from_path(str(path))
        assert ticker == "AMZN"

    def test_extract_ticker_invalid_path_raises_error(self):
        """Test that invalid path raises ValueError."""
        with pytest.raises(ValueError, match="Ticker symbol not found"):
            extract_ticker_from_path("not_a_stock_path.txt")

    def test_extract_ticker_no_csv(self):
        """Test extracting ticker from non-CSV file."""
        # The function should still work if the pattern matches
        # or raise ValueError if it doesn't
        try:
            ticker = extract_ticker_from_path("data/NFLX.parquet")
            # If it works, check the result
            assert ticker == "NFLX"
        except ValueError:
            # If it raises ValueError, that's also acceptable
            pass
