"""Tests for ai_trader.backtesting.feeds.fxmacrodata_calendar."""

import json
from unittest.mock import patch

import pytest

from ai_trader.backtesting.feeds.fxmacrodata_calendar import FXMacroDataCalendarFeed


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


@patch("ai_trader.backtesting.feeds.fxmacrodata_calendar.urlopen")
def test_api_key_is_not_forwarded_on_redirect(mock_urlopen):
    mock_urlopen.return_value = FakeResponse({"data": [{"market_tier": 1}]})

    rows = FXMacroDataCalendarFeed(api_key="test-key").calendar()

    # urllib copies request.headers onto a redirected request, but not unredirected headers.
    request = mock_urlopen.call_args[0][0]
    assert request.unredirected_hdrs["X-api-key"] == "test-key"
    assert "X-api-key" not in request.headers
    assert rows == [{"market_tier": 1}]


def test_invalid_api_key_error_does_not_include_key():
    with pytest.raises(ValueError) as excinfo:
        FXMacroDataCalendarFeed(api_key="test\nkey")

    assert "test" not in str(excinfo.value)


@patch("ai_trader.backtesting.feeds.fxmacrodata_calendar.urlopen")
def test_error_body_raises_clean_error(mock_urlopen):
    mock_urlopen.return_value = FakeResponse({"detail": "Invalid API key"})

    with pytest.raises(ValueError, match="Invalid API key"):
        FXMacroDataCalendarFeed(api_key="test-key").calendar()
