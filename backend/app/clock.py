"""Timezone-aware UTC clock used by application services and tests."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol


class Clock(Protocol):
    """Small clock interface that can be replaced by a deterministic test clock."""

    def now(self) -> datetime:
        """Return the current timezone-aware UTC time."""


class UtcClock:
    """Production clock implementation."""

    def now(self) -> datetime:
        return datetime.now(timezone.utc)


def utc_now(clock: Clock | None = None) -> datetime:
    """Return a timezone-aware UTC value from the supplied or production clock."""

    value = (clock or UtcClock()).now()
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("The application clock must return a timezone-aware datetime.")
    return value.astimezone(timezone.utc)
