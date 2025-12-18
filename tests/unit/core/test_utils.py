"""Tests for ai_trader.core.utils module."""

import pytest
from ai_trader.core.utils import check_rules, extract_ticker_from_path


class TestCheckRules:
    """Test the check_rules function."""

    def test_all_conditions_true_cutoff_zero(self):
        """Test with all True conditions and cutoff=0."""
        result = check_rules([True, True, True], cutoff=0)
        assert result is True

    def test_all_conditions_false_cutoff_zero(self):
        """Test with all False conditions and cutoff=0."""
        result = check_rules([False, False, False], cutoff=0)
        assert result is True

    def test_mixed_conditions_cutoff_met(self):
        """Test with mixed conditions where cutoff is met."""
        result = check_rules([True, False, False, True], cutoff=2)
        assert result is True

    def test_mixed_conditions_cutoff_not_met(self):
        """Test with mixed conditions where cutoff is not met."""
        result = check_rules([True, False, True, True], cutoff=3)
        assert result is False

    def test_exactly_one_false_cutoff_one(self):
        """Test with exactly one False when cutoff is 1."""
        result = check_rules([True, False, True], cutoff=1)
        assert result is True

    def test_empty_list(self):
        """Test with empty list."""
        result = check_rules([], cutoff=0)
        assert result is True

    def test_empty_list_with_cutoff(self):
        """Test with empty list and positive cutoff."""
        result = check_rules([], cutoff=1)
        assert result is False

    def test_single_true(self):
        """Test with single True."""
        result = check_rules([True], cutoff=0)
        assert result is True
        result = check_rules([True], cutoff=1)
        assert result is False

    def test_single_false(self):
        """Test with single False."""
        result = check_rules([False], cutoff=0)
        assert result is True
        result = check_rules([False], cutoff=1)
        assert result is True

    @pytest.mark.parametrize("conds,cutoff,expected", [
        ([True, True, True], 0, True),
        ([False, False, False], 3, True),
        ([False, False, False], 4, False),
        ([True, False], 1, True),
        ([True, False], 2, False),
        ([True, False, True, False, True], 2, True),
        ([True, False, True, False, True], 3, False),
    ])
    def test_various_combinations(self, conds, cutoff, expected):
        """Test various combinations of conditions and cutoffs."""
        assert check_rules(conds, cutoff) == expected

    def test_large_list_all_true(self):
        """Test with large list of all True."""
        conds = [True] * 1000
        assert check_rules(conds, cutoff=1) is False
        assert check_rules(conds, cutoff=0) is True

    def test_large_list_with_few_false(self):
        """Test with large list with few False."""
        conds = [True] * 999 + [False, False, False]
        assert check_rules(conds, cutoff=3) is True
        assert check_rules(conds, cutoff=4) is False

    def test_docstring_example(self):
        """Test the example from docstring."""
        result = check_rules([True, False, False, True], cutoff=2)
        assert result is True


class TestExtractTickerFromPath:
    """Test the extract_ticker_from_path function."""

    @pytest.mark.parametrize("file_path,expected", [
        ("data/AAPL.csv", "AAPL"),
        ("data/us_stock/AAPL.csv", "AAPL"),
        ("data/MSFT.csv", "MSFT"),
        ("data/GOOGL.csv", "GOOGL"),
        ("/absolute/path/AAPL.csv", "AAPL"),
    ])
    def test_us_stock_paths(self, file_path, expected):
        """Test extraction of US stock tickers."""
        assert extract_ticker_from_path(file_path) == expected

    @pytest.mark.parametrize("file_path,expected", [
        ("data/2330.csv", "2330"),
        ("data/tw_stock/2330.csv", "2330"),
        ("data/1301.csv", "1301"),
        ("/absolute/path/tw/2330.csv", "2330"),
    ])
    def test_tw_stock_paths(self, file_path, expected):
        """Test extraction of Taiwan stock tickers."""
        assert extract_ticker_from_path(file_path) == expected

    @pytest.mark.parametrize("file_path,expected", [
        ("data/BTC-USD.csv", "BTC-USD"),
        ("data/crypto/ETH-USD.csv", "ETH-USD"),
        ("data/EURUSD.csv", "EURUSD"),
    ])
    def test_crypto_and_forex_paths(self, file_path, expected):
        """Test extraction of crypto and forex tickers."""
        assert extract_ticker_from_path(file_path) == expected

    @pytest.mark.parametrize("file_path", [
        "data/",
        "data.csv",
        "AAPL.csv",
        "data/missing.txt",
        "path/without/csv.extension",
        "/path/without/filename.csv/",
        "no_slash_before_filename.csv",
    ])
    def test_invalid_paths_raise_error(self, file_path):
        """Test that invalid paths raise ValueError."""
        with pytest.raises(ValueError, match="Ticker symbol not found"):
            extract_ticker_from_path(file_path)

    def test_docstring_example_us(self):
        """Test the US example from docstring."""
        result = extract_ticker_from_path("data/us_stock/AAPL.csv")
        assert result == "AAPL"

    def test_docstring_example_tw(self):
        """Test the TW example from docstring."""
        result = extract_ticker_from_path("data/tw_stock/2330.csv")
        assert result == "2330"

    def test_special_characters_in_ticker(self):
        """Test tickers with special characters."""
        result = extract_ticker_from_path("data/BRK.B.csv")
        assert result == "BRK.B"

    def test_complex_paths(self):
        """Test with complex directory structures."""
        paths = [
            "/home/user/ai-trader/data/us_stock/AAPL.csv",
            "../../data/tw_stock/2330.csv",
            "./data/crypto/BTC-USD.csv",
        ]
        expected = ["AAPL", "2330", "BTC-USD"]

        for path, ticker in zip(paths, expected):
            assert extract_ticker_from_path(path) == ticker

    def test_uppercase_lowercase_preserved(self):
        """Test that case is preserved."""
        assert extract_ticker_from_path("data/aapl.csv") == "aapl"
        assert extract_ticker_from_path("data/AAPL.csv") == "AAPL"
        assert extract_ticker_from_path("data/AaPl.csv") == "AaPl"

    def test_numbers_only_ticker(self):
        """Test ticker with numbers only."""
        assert extract_ticker_from_path("data/2330.csv") == "2330"
        assert extract_ticker_from_path("data/1234567.csv") == "1234567"

    def test_underscore_in_ticker(self):
        """Test ticker with underscore."""
        assert extract_ticker_from_path("data/BRK_A.csv") == "BRK_A"

    def test_hyphen_in_ticker(self):
        """Test ticker with hyphen."""
        assert extract_ticker_from_path("data/BTC-USD.csv") == "BTC-USD"

    def test_error_message(self):
        """Test the error message content."""
        with pytest.raises(ValueError) as exc_info:
            extract_ticker_from_path("invalid_path")

        assert "Ticker symbol not found" in str(exc_info.value)

    def test_multiple_slashes_in_path(self):
        """Test paths with multiple directory levels."""
        result = extract_ticker_from_path("data/markets/us_stock/2024/AAPL.csv")
        assert result == "AAPL"

    def test_filename_with_underscore(self):
        """Test filename with underscores."""
        result = extract_ticker_from_path("data/US_STOCK_AAPL.csv")
        assert result == "US_STOCK_AAPL"
