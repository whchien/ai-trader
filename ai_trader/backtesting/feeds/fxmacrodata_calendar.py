from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class FXMacroDataCalendarFeed:
    """Small macro-calendar feed for backtest event filters."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.fxmacrodata.com/v1",
        timeout: int = 20,
    ) -> None:
        self.api_key = _clean_api_key(api_key if api_key is not None else os.getenv("FXMD_API_KEY"))
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def calendar(
        self,
        currency: str = "usd",
        start_date: str | None = None,
        end_date: str | None = None,
        top_tier_only: bool = False,
    ) -> list[dict[str, Any]]:
        params: dict[str, str] = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        query = f"?{urlencode(params)}" if params else ""
        headers = {"Accept": "application/json", "User-Agent": "ai-trader-fxmacrodata"}
        request = Request(f"{self.base_url}/calendar/{currency.lower()}{query}", headers=headers)
        if self.api_key:
            # Unredirected, so urllib never forwards the key on a redirect to another host.
            request.add_unredirected_header("X-API-Key", self.api_key)
        with urlopen(request, timeout=self.timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, list):
            detail = payload.get("detail") if isinstance(payload, dict) else None
            raise ValueError(f"Unexpected FXMacroData calendar response{f': {detail}' if detail else ''}")
        rows = [row for row in data if isinstance(row, dict)]
        if top_tier_only:
            rows = [
                row
                for row in rows
                if row.get("top_tier_for_currency") or row.get("market_tier") == 1
            ]
        return rows

    def has_event_near(
        self,
        timestamp: datetime,
        currency: str = "usd",
        before: timedelta = timedelta(hours=4),
        after: timedelta = timedelta(hours=2),
    ) -> bool:
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        rows = self.calendar(
            currency=currency,
            start_date=(timestamp - before).date().isoformat(),
            end_date=(timestamp + after).date().isoformat(),
            top_tier_only=True,
        )
        for row in rows:
            event_time = _parse_event_time(row)
            if event_time and event_time - before <= timestamp <= event_time + after:
                return True
        return False


def _clean_api_key(api_key: str | None) -> str | None:
    if not api_key:
        return None
    api_key = api_key.strip()
    if any(char.isspace() or not char.isprintable() for char in api_key):
        # Keep the key itself out of the message.
        raise ValueError("FXMacroData API key contains whitespace or control characters")
    return api_key or None


def _parse_event_time(row: dict[str, Any]) -> datetime | None:
    value = row.get("announcement_datetime_utc") or row.get("announcement_datetime_local")
    if not value:
        return None
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
