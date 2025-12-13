"""Custom exceptions for ai-trader."""


class AITraderError(Exception):
    """Base exception for all ai-trader errors."""

    pass


class DataError(AITraderError):
    """Base class for data-related errors."""

    pass


class DataFetchError(DataError):
    """Raised when data fetching fails."""

    def __init__(self, message: str, symbol: str = None, source: str = None):
        self.symbol = symbol
        self.source = source
        super().__init__(message)


class DataValidationError(DataError):
    """Raised when data validation fails."""

    def __init__(self, message: str, symbol: str = None, issues: list = None):
        self.symbol = symbol
        self.issues = issues or []
        super().__init__(message)


class StrategyError(AITraderError):
    """Raised when strategy execution fails."""

    pass


class ConfigurationError(AITraderError):
    """Raised when configuration is invalid."""

    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(message)
