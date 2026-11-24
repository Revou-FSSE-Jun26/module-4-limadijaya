"""Injectable UTC clock (DB-04). Services read the time only through utcnow()."""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone

_provider: Callable[[], datetime] | None = None


def utcnow() -> datetime:
    """Return the current time as a timezone-aware UTC datetime."""
    if _provider is not None:
        value = _provider()
        if value.tzinfo is None:
            raise ValueError("The injected clock must return a timezone-aware datetime.")
        return value.astimezone(timezone.utc)
    return datetime.now(timezone.utc)


def set_clock(provider: Callable[[], datetime] | None) -> None:
    """Replace the clock (tests only). Pass None to restore the real clock."""
    global _provider
    _provider = provider
