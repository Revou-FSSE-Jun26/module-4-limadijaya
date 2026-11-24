"""Environment-backed Flask configuration."""

from __future__ import annotations

import os
from datetime import timedelta


MAX_CONTENT_LENGTH = 1_048_576


def _required(name: str) -> str:
    value = os.environ.get(name)
    if value is None or value == "":
        raise RuntimeError(f"Required environment variable {name} is not set.")
    return value


def _optional_int(name: str) -> int | None:
    value = os.environ.get(name)
    if value is None or value == "":
        return None
    try:
        parsed = int(value)
    except ValueError as exc:
        raise RuntimeError(f"Environment variable {name} must be an integer.") from exc
    if parsed < 0:
        raise RuntimeError(f"Environment variable {name} must not be negative.")
    return parsed


def _engine_options() -> dict[str, int | bool]:
    options: dict[str, int | bool] = {"pool_pre_ping": True}
    pool_size = _optional_int("DB_POOL_SIZE")
    max_overflow = _optional_int("DB_MAX_OVERFLOW")
    if pool_size is not None:
        options["pool_size"] = pool_size
    if max_overflow is not None:
        options["max_overflow"] = max_overflow
    return options


def environment_config() -> dict[str, object]:
    """Build the production configuration, failing fast for required settings."""

    try:
        expires_seconds = int(_required("JWT_ACCESS_TOKEN_EXPIRES_SECONDS"))
    except ValueError as exc:
        raise RuntimeError(
            "Environment variable JWT_ACCESS_TOKEN_EXPIRES_SECONDS must be an integer."
        ) from exc
    if expires_seconds <= 0:
        raise RuntimeError("Environment variable JWT_ACCESS_TOKEN_EXPIRES_SECONDS must be positive.")

    return {
        "SQLALCHEMY_DATABASE_URI": _required("DATABASE_URL"),
        "SQLALCHEMY_ENGINE_OPTIONS": _engine_options(),
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "JWT_SECRET_KEY": _required("JWT_SECRET_KEY"),
        "JWT_ACCESS_TOKEN_EXPIRES": timedelta(seconds=expires_seconds),
        "JWT_TOKEN_LOCATION": ["headers"],
        "FRONTEND_ORIGIN": _required("FRONTEND_ORIGIN"),
        "LOG_LEVEL": os.environ.get("LOG_LEVEL", "INFO"),
        "MAX_CONTENT_LENGTH": MAX_CONTENT_LENGTH,
    }
