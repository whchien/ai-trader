"""Tests for ai_trader.core.exceptions module."""

import pytest
from ai_trader.core.exceptions import (
    AITraderError,
    DataError,
    DataFetchError,
    DataValidationError,
    StrategyError,
    ConfigurationError,
)


class TestExceptionHierarchy:
    """Test exception inheritance hierarchy."""

    def test_data_error_inherits_from_ai_trader_error(self):
        """Test that DataError is a subclass of AITraderError."""
        assert issubclass(DataError, AITraderError)

    def test_data_fetch_error_inherits_from_data_error(self):
        """Test that DataFetchError is a subclass of DataError."""
        assert issubclass(DataFetchError, DataError)

    def test_data_validation_error_inherits_from_data_error(self):
        """Test that DataValidationError is a subclass of DataError."""
        assert issubclass(DataValidationError, DataError)

    def test_strategy_error_inherits_from_ai_trader_error(self):
        """Test that StrategyError is a subclass of AITraderError."""
        assert issubclass(StrategyError, AITraderError)

    def test_configuration_error_inherits_from_ai_trader_error(self):
        """Test that ConfigurationError is a subclass of AITraderError."""
        assert issubclass(ConfigurationError, AITraderError)


class TestAITraderError:
    """Test AITraderError base exception."""

    def test_can_be_raised_and_caught(self):
        """Test that AITraderError can be raised and caught."""
        with pytest.raises(AITraderError):
            raise AITraderError("Test error")

    def test_message_is_preserved(self):
        """Test that error message is preserved."""
        error_msg = "This is a test error"
        with pytest.raises(AITraderError, match=error_msg):
            raise AITraderError(error_msg)


class TestDataError:
    """Test DataError base exception."""

    def test_can_be_raised_and_caught(self):
        """Test that DataError can be raised and caught."""
        with pytest.raises(DataError):
            raise DataError("Data error test")

    def test_caught_as_ai_trader_error(self):
        """Test that DataError can be caught as AITraderError."""
        with pytest.raises(AITraderError):
            raise DataError("Data error")


class TestDataFetchError:
    """Test DataFetchError exception."""

    def test_stores_symbol_attribute(self):
        """Test that symbol attribute is stored."""
        error = DataFetchError("Fetch failed", symbol="AAPL")
        assert error.symbol == "AAPL"

    def test_stores_source_attribute(self):
        """Test that source attribute is stored."""
        error = DataFetchError("Fetch failed", source="yfinance")
        assert error.source == "yfinance"

    def test_stores_both_symbol_and_source(self):
        """Test that both symbol and source are stored."""
        error = DataFetchError("Fetch failed", symbol="MSFT", source="twstock")
        assert error.symbol == "MSFT"
        assert error.source == "twstock"

    def test_symbol_defaults_to_none(self):
        """Test that symbol defaults to None."""
        error = DataFetchError("Fetch failed")
        assert error.symbol is None

    def test_source_defaults_to_none(self):
        """Test that source defaults to None."""
        error = DataFetchError("Fetch failed")
        assert error.source is None

    def test_message_is_preserved(self):
        """Test that error message is preserved."""
        error_msg = "Failed to fetch data for AAPL"
        error = DataFetchError(error_msg, symbol="AAPL")
        assert str(error) == error_msg

    def test_can_be_caught_as_data_error(self):
        """Test that DataFetchError can be caught as DataError."""
        with pytest.raises(DataError):
            raise DataFetchError("Fetch failed", symbol="AAPL")

    def test_can_be_caught_as_ai_trader_error(self):
        """Test that DataFetchError can be caught as AITraderError."""
        with pytest.raises(AITraderError):
            raise DataFetchError("Fetch failed")

    @pytest.mark.parametrize("symbol,source", [
        ("AAPL", "yfinance"),
        ("2330.TW", "twstock"),
        ("BTC-USD", "yfinance"),
        (None, "yfinance"),
        ("AAPL", None),
    ])
    def test_various_symbol_source_combinations(self, symbol, source):
        """Test various symbol and source combinations."""
        error = DataFetchError("Test", symbol=symbol, source=source)
        assert error.symbol == symbol
        assert error.source == source


class TestDataValidationError:
    """Test DataValidationError exception."""

    def test_stores_symbol_attribute(self):
        """Test that symbol attribute is stored."""
        error = DataValidationError("Validation failed", symbol="AAPL")
        assert error.symbol == "AAPL"

    def test_stores_issues_list(self):
        """Test that issues list is stored."""
        issues = ["missing open column", "all NaN values"]
        error = DataValidationError("Validation failed", issues=issues)
        assert error.issues == issues

    def test_stores_symbol_and_issues(self):
        """Test that both symbol and issues are stored."""
        issues = ["missing volume", "negative prices"]
        error = DataValidationError("Invalid data", symbol="MSFT", issues=issues)
        assert error.symbol == "MSFT"
        assert error.issues == issues

    def test_issues_defaults_to_empty_list(self):
        """Test that issues defaults to empty list."""
        error = DataValidationError("Validation failed")
        assert error.issues == []

    def test_symbol_defaults_to_none(self):
        """Test that symbol defaults to None."""
        error = DataValidationError("Validation failed")
        assert error.symbol is None

    def test_empty_issues_list_parameter(self):
        """Test with explicit empty issues list."""
        error = DataValidationError("Test", issues=[])
        assert error.issues == []

    def test_message_is_preserved(self):
        """Test that error message is preserved."""
        error_msg = "Data validation failed for AAPL"
        error = DataValidationError(error_msg, symbol="AAPL")
        assert str(error) == error_msg

    def test_can_be_caught_as_data_error(self):
        """Test that DataValidationError can be caught as DataError."""
        with pytest.raises(DataError):
            raise DataValidationError("Validation failed")

    def test_can_be_caught_as_ai_trader_error(self):
        """Test that DataValidationError can be caught as AITraderError."""
        with pytest.raises(AITraderError):
            raise DataValidationError("Validation failed")

    @pytest.mark.parametrize("issues", [
        ["missing open"],
        ["missing open", "missing close"],
        ["missing open", "missing close", "all NaN"],
    ])
    def test_various_issues_lists(self, issues):
        """Test various issues lists."""
        error = DataValidationError("Failed", issues=issues)
        assert error.issues == issues


class TestStrategyError:
    """Test StrategyError exception."""

    def test_can_be_raised_and_caught(self):
        """Test that StrategyError can be raised and caught."""
        with pytest.raises(StrategyError):
            raise StrategyError("Strategy execution failed")

    def test_caught_as_ai_trader_error(self):
        """Test that StrategyError can be caught as AITraderError."""
        with pytest.raises(AITraderError):
            raise StrategyError("Strategy execution failed")

    def test_message_is_preserved(self):
        """Test that error message is preserved."""
        error_msg = "Strategy parameter validation failed"
        with pytest.raises(StrategyError, match=error_msg):
            raise StrategyError(error_msg)


class TestConfigurationError:
    """Test ConfigurationError exception."""

    def test_stores_field_attribute(self):
        """Test that field attribute is stored."""
        error = ConfigurationError("Invalid config", field="broker.cash")
        assert error.field == "broker.cash"

    def test_field_defaults_to_none(self):
        """Test that field defaults to None."""
        error = ConfigurationError("Invalid config")
        assert error.field is None

    def test_message_is_preserved(self):
        """Test that error message is preserved."""
        error_msg = "Configuration validation failed"
        error = ConfigurationError(error_msg, field="data.market")
        assert str(error) == error_msg

    def test_caught_as_ai_trader_error(self):
        """Test that ConfigurationError can be caught as AITraderError."""
        with pytest.raises(AITraderError):
            raise ConfigurationError("Config error")

    @pytest.mark.parametrize("field", [
        "broker.cash",
        "data.market",
        "backtest.start_date",
        None,
    ])
    def test_various_field_values(self, field):
        """Test various field values."""
        error = ConfigurationError("Config error", field=field)
        assert error.field == field


class TestExceptionRaising:
    """Test raising and catching exceptions in realistic scenarios."""

    def test_catch_data_error_from_fetch_or_validation(self):
        """Test catching DataError from either fetch or validation error."""
        def simulate_fetch():
            raise DataFetchError("Network error", symbol="AAPL", source="yfinance")

        def simulate_validate():
            raise DataValidationError("Invalid data", symbol="AAPL")

        # Catch fetch error
        with pytest.raises(DataError):
            simulate_fetch()

        # Catch validation error
        with pytest.raises(DataError):
            simulate_validate()

    def test_catch_all_errors_as_ai_trader_error(self):
        """Test catching all exceptions as AITraderError."""
        errors = [
            DataFetchError("Fetch failed"),
            DataValidationError("Validation failed"),
            StrategyError("Strategy failed"),
            ConfigurationError("Config failed"),
        ]

        for error in errors:
            with pytest.raises(AITraderError):
                raise error

    def test_exception_with_context_chain(self):
        """Test exception chaining with context."""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise DataFetchError(
                    f"Failed to fetch: {str(e)}",
                    symbol="AAPL"
                ) from e
        except DataFetchError as e:
            assert e.symbol == "AAPL"
            assert e.__cause__ is not None
