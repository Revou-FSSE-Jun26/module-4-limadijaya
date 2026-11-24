"""Configuration read from the environment. Missing required values stop start-up (BE-01, NFR-010-AC03).

No secret has a default in code. The token lifetime has no default either (UD-01).
"""
from __future__ import annotations

import os
from collections.abc import Mapping

MAX_BODY_BYTES = 1_048_576  # DA-07: 1 MiB JSON request body limit

REQUIRED_VARIABLES = (
    "DATABASE_URL",
    "JWT_SECRET_KEY",
    "JWT_ACCESS_TOKEN_EXPIRES_SECONDS",
    "FRONTEND_ORIGIN",
)


class ConfigError(RuntimeError):
    """A required configuration value is missing or invalid."""


def _normalize_database_url(url: str) -> str:
    # Some hosts still hand out postgres:// URLs, which SQLAlchemy 2 rejects.
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://"):]
    return url


def build_config(overrides: Mapping[str, object] | None = None) -> dict[str, object]:
    """Build the Flask config from overrides first, then os.environ."""
    overrides = dict(overrides or {})
    values: dict[str, str] = {}
    for name in REQUIRED_VARIABLES:
        raw = overrides.get(name, os.environ.get(name))
        if raw is None or str(raw).strip() == "":
            raise ConfigError(f"Missing required environment variable: {name}")
        values[name] = str(raw).strip()

    try:
        lifetime = int(values["JWT_ACCESS_TOKEN_EXPIRES_SECONDS"])
    except ValueError:
        raise ConfigError("JWT_ACCESS_TOKEN_EXPIRES_SECONDS must be an integer number of seconds") from None
    if lifetime <= 0:
        raise ConfigError("JWT_ACCESS_TOKEN_EXPIRES_SECONDS must be greater than zero")

    pool_size = int(overrides.get("DB_POOL_SIZE", os.environ.get("DB_POOL_SIZE", 3)))
    max_overflow = int(overrides.get("DB_MAX_OVERFLOW", os.environ.get("DB_MAX_OVERFLOW", 2)))

    config: dict[str, object] = {
        "SQLALCHEMY_DATABASE_URI": _normalize_database_url(values["DATABASE_URL"]),
        "SQLALCHEMY_ENGINE_OPTIONS": {
            "pool_pre_ping": True,
            "pool_size": pool_size,
            "max_overflow": max_overflow,
        },
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "JWT_SECRET_KEY": values["JWT_SECRET_KEY"],
        "JWT_TOKEN_LOCATION": ["headers"],
        "JWT_ACCESS_TOKEN_EXPIRES": lifetime,
        "FRONTEND_ORIGIN": values["FRONTEND_ORIGIN"],
        "LOG_LEVEL": str(overrides.get("LOG_LEVEL", os.environ.get("LOG_LEVEL", "INFO"))).upper(),
        "MAX_CONTENT_LENGTH": MAX_BODY_BYTES,
        "JSON_SORT_KEYS": False,
        "TESTING": bool(overrides.get("TESTING", False)),
    }
    return config
