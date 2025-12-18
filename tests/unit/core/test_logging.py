"""Tests for ai_trader.core.logging module."""

import logging
import pytest
from pathlib import Path
from ai_trader.core.logging import setup_logger, get_logger


@pytest.fixture(autouse=True)
def reset_logging():
    """Reset logging configuration between tests."""
    # Clear root logger handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Clear all named loggers
    for logger_name in list(logging.Logger.manager.loggerDict):
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.setLevel(logging.WARNING)

    yield

    # Clean up after test
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    for logger_name in list(logging.Logger.manager.loggerDict):
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()


class TestSetupLogger:
    """Test the setup_logger function."""

    def test_creates_logger_with_default_config(self):
        """Test creating a logger with default configuration."""
        logger = setup_logger("test_logger")
        assert logger is not None
        assert logger.name == "test_logger"

    def test_sets_correct_log_level(self):
        """Test that log level is set correctly."""
        logger = setup_logger("test_logger", level="DEBUG")
        assert logger.level == logging.DEBUG

        logger2 = setup_logger("test_logger2", level="ERROR")
        assert logger2.level == logging.ERROR

    @pytest.mark.parametrize("level_str,level_int", [
        ("DEBUG", logging.DEBUG),
        ("INFO", logging.INFO),
        ("WARNING", logging.WARNING),
        ("ERROR", logging.ERROR),
        ("CRITICAL", logging.CRITICAL),
    ])
    def test_various_log_levels(self, level_str, level_int):
        """Test setting various log levels."""
        logger = setup_logger(f"test_{level_str}", level=level_str)
        assert logger.level == level_int

    def test_lowercase_level_string(self):
        """Test that lowercase level strings are converted."""
        logger = setup_logger("test_logger", level="info")
        assert logger.level == logging.INFO

    def test_adds_console_handler(self):
        """Test that console handler is added."""
        logger = setup_logger("test_logger")
        handlers = logger.handlers
        assert len(handlers) > 0
        assert any(isinstance(h, logging.StreamHandler) for h in handlers)

    def test_console_handler_has_formatter(self):
        """Test that console handler has a formatter."""
        logger = setup_logger("test_logger")
        console_handler = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)][0]
        assert console_handler.formatter is not None

    def test_uses_default_format(self):
        """Test that default format is used when not specified."""
        logger = setup_logger("test_logger")
        console_handler = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)][0]
        formatter_format = console_handler.formatter._fmt
        assert "%(asctime)s" in formatter_format
        assert "%(name)s" in formatter_format
        assert "%(levelname)s" in formatter_format
        assert "%(message)s" in formatter_format

    def test_custom_format_string(self):
        """Test that custom format string is applied."""
        custom_format = "%(levelname)s - %(message)s"
        logger = setup_logger("test_logger", format_string=custom_format)
        console_handler = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)][0]
        assert console_handler.formatter._fmt == custom_format

    def test_creates_log_file(self, tmp_path):
        """Test that log file is created when specified."""
        log_file = tmp_path / "test.log"
        logger = setup_logger("test_logger", log_file=log_file)

        # Log something
        logger.info("Test message")

        # Check file was created
        assert log_file.exists()

    def test_creates_parent_directories_for_log_file(self, tmp_path):
        """Test that parent directories are created for log file."""
        log_file = tmp_path / "logs" / "subdir" / "test.log"
        logger = setup_logger("test_logger", log_file=log_file)

        # Log something to ensure file is created
        logger.info("Test message")

        assert log_file.exists()
        assert log_file.parent.exists()

    def test_adds_file_handler_when_log_file_provided(self, tmp_path):
        """Test that file handler is added when log file is provided."""
        log_file = tmp_path / "test.log"
        logger = setup_logger("test_logger", log_file=log_file)

        # Should have console handler + file handler
        assert len(logger.handlers) >= 2
        assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)

    def test_logs_to_file(self, tmp_path):
        """Test that logs are written to file."""
        log_file = tmp_path / "test.log"
        logger = setup_logger("test_logger", log_file=log_file)

        test_message = "Test log message"
        logger.info(test_message)

        # Read log file
        with open(log_file) as f:
            content = f.read()
        assert test_message in content

    def test_avoids_duplicate_handlers(self):
        """Test that duplicate handlers are not added on multiple calls."""
        logger = setup_logger("test_logger")
        handlers_count = len(logger.handlers)

        # Call setup_logger again with same name
        logger2 = setup_logger("test_logger")
        assert logger2 is logger
        assert len(logger.handlers) == handlers_count

    def test_returns_logger_instance(self):
        """Test that a logger instance is returned."""
        logger = setup_logger("test_logger")
        assert isinstance(logger, logging.Logger)

    def test_logger_can_log_messages(self, caplog):
        """Test that the configured logger can log messages."""
        logger = setup_logger("test_logger", level="INFO")

        with caplog.at_level(logging.INFO):
            logger.info("Test message")

        assert "Test message" in caplog.text

    def test_logging_at_different_levels(self, caplog):
        """Test logging at different levels."""
        logger = setup_logger("test_logger", level="DEBUG")

        with caplog.at_level(logging.DEBUG):
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")

        assert "Debug message" in caplog.text
        assert "Info message" in caplog.text
        assert "Warning message" in caplog.text
        assert "Error message" in caplog.text

    def test_docstring_example(self, tmp_path):
        """Test the example from docstring."""
        log_file = tmp_path / "app.log"
        logger = setup_logger(__name__, level="DEBUG", log_file=log_file)
        logger.info("Application started")
        assert log_file.exists()


class TestGetLogger:
    """Test the get_logger function."""

    def test_returns_logger_instance(self):
        """Test that get_logger returns a logger instance."""
        logger = get_logger("test_logger")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"

    def test_sets_default_log_level(self):
        """Test that default log level is set."""
        logger = get_logger("test_logger")
        assert logger.level == logging.INFO

    def test_custom_log_level(self):
        """Test setting custom log level."""
        logger = get_logger("test_logger", level="DEBUG")
        assert logger.level == logging.DEBUG

    def test_returns_same_logger_on_subsequent_calls(self):
        """Test that the same logger is returned on subsequent calls."""
        logger1 = get_logger("test_logger")
        logger2 = get_logger("test_logger")
        assert logger1 is logger2

    def test_configures_logger_if_not_configured(self):
        """Test that logger is configured if not already configured."""
        logger = get_logger("test_logger")
        assert len(logger.handlers) > 0

    def test_returns_existing_if_already_configured(self):
        """Test that existing configured logger is returned."""
        # First call configures the logger
        logger1 = get_logger("test_logger")
        handlers_count = len(logger1.handlers)

        # Second call returns existing logger without reconfiguring
        logger2 = get_logger("test_logger")
        assert logger2 is logger1
        assert len(logger2.handlers) == handlers_count

    def test_different_loggers_are_different(self):
        """Test that different logger names return different logger instances."""
        logger1 = get_logger("logger1")
        logger2 = get_logger("logger2")
        assert logger1 is not logger2
        assert logger1.name != logger2.name

    def test_can_log_messages(self, caplog):
        """Test that logger can log messages."""
        logger = get_logger("test_logger", level="INFO")

        with caplog.at_level(logging.INFO):
            logger.info("Test message")

        assert "Test message" in caplog.text

    def test_docstring_example(self, caplog):
        """Test the example from docstring."""
        logger = get_logger(__name__)
        with caplog.at_level(logging.INFO):
            logger.info("Processing data")
        assert "Processing data" in caplog.text

    @pytest.mark.parametrize("logger_name", [
        "ai_trader",
        "ai_trader.core",
        "ai_trader.data.fetchers",
        "custom_logger",
    ])
    def test_various_logger_names(self, logger_name):
        """Test creating loggers with various names."""
        logger = get_logger(logger_name)
        assert logger.name == logger_name
        assert isinstance(logger, logging.Logger)


class TestLoggingIntegration:
    """Integration tests for logging module."""

    def test_setup_and_get_logger_consistency(self):
        """Test that setup_logger and get_logger work consistently."""
        logger1 = setup_logger("test_logger", level="DEBUG")
        logger2 = get_logger("test_logger")

        # They should be the same logger
        assert logger1.name == logger2.name

    def test_multiple_loggers_independent(self):
        """Test that multiple loggers are independent."""
        logger1 = setup_logger("logger1", level="DEBUG")
        logger2 = setup_logger("logger2", level="ERROR")

        assert logger1.level != logger2.level
        assert logger1.name != logger2.name

    def test_logging_with_file_and_console(self, tmp_path, caplog):
        """Test logging to both file and console."""
        log_file = tmp_path / "test.log"
        logger = setup_logger("test_logger", log_file=log_file)

        test_message = "Test message"
        with caplog.at_level(logging.INFO):
            logger.info(test_message)

        # Check console output
        assert test_message in caplog.text

        # Check file output
        with open(log_file) as f:
            file_content = f.read()
        assert test_message in file_content
