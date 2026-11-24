"""Acceptance tests for the T2.01 application foundation."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app import create_app, get_clock
from app.config import environment_config


REQUIRED_ENVIRONMENT = {
    "DATABASE_URL": "postgresql://app@example.invalid/revotask",
    "JWT_SECRET_KEY": "test-only-secret",
    "JWT_ACCESS_TOKEN_EXPIRES_SECONDS": "900",
    "FRONTEND_ORIGIN": "http://localhost:3000",
}


class FixedClock:
    def __init__(self, value: datetime):
        self.value = value

    def now(self) -> datetime:
        return self.value


def test_environment_config_requires_each_required_variable(monkeypatch):
    for name in REQUIRED_ENVIRONMENT:
        for variable, value in REQUIRED_ENVIRONMENT.items():
            monkeypatch.setenv(variable, value)
        monkeypatch.delenv(name)

        with pytest.raises(RuntimeError, match=name):
            environment_config()


def test_environment_config_sets_required_limits_and_pool_options(monkeypatch):
    for name, value in REQUIRED_ENVIRONMENT.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setenv("DB_POOL_SIZE", "3")
    monkeypatch.setenv("DB_MAX_OVERFLOW", "1")

    config = environment_config()

    assert config["MAX_CONTENT_LENGTH"] == 1_048_576
    assert config["SQLALCHEMY_ENGINE_OPTIONS"] == {
        "pool_pre_ping": True,
        "pool_size": 3,
        "max_overflow": 1,
    }


def test_create_app_uses_a_replaceable_timezone_aware_clock():
    fixed = FixedClock(datetime(2026, 11, 24, 12, 0, tzinfo=timezone.utc))
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "postgresql://app@example.invalid/revotask",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "JWT_SECRET_KEY": "test-only-secret",
            "JWT_ACCESS_TOKEN_EXPIRES": 900,
            "FRONTEND_ORIGIN": "http://localhost:3000",
            "MAX_CONTENT_LENGTH": 1_048_576,
            "CLOCK": fixed,
        }
    )

    assert get_clock(app) is fixed
    assert get_clock(app).now().tzinfo == timezone.utc
