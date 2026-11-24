"""Pure unit tests: configuration, clock, StrictNumber, and password hashing (no database)."""
from datetime import datetime, timezone

import pytest
from marshmallow import ValidationError

from app import clock
from app.config import REQUIRED_VARIABLES, ConfigError, build_config
from app.schemas_common import StrictNumber, iso
from app.security import hash_password, verify_password

VALID = {
    "DATABASE_URL": "postgresql://u:p@localhost:5432/x",
    "JWT_SECRET_KEY": "secret",
    "JWT_ACCESS_TOKEN_EXPIRES_SECONDS": "60",
    "FRONTEND_ORIGIN": "http://localhost:3000",
}


@pytest.mark.parametrize("missing", REQUIRED_VARIABLES)
def test_missing_required_variable_names_the_variable(monkeypatch, missing):
    for name in REQUIRED_VARIABLES:
        monkeypatch.delenv(name, raising=False)
    overrides = {k: v for k, v in VALID.items() if k != missing}
    with pytest.raises(ConfigError, match=missing):
        build_config(overrides)


def test_token_lifetime_has_no_default_and_must_be_positive():
    with pytest.raises(ConfigError):
        build_config({**VALID, "JWT_ACCESS_TOKEN_EXPIRES_SECONDS": "0"})
    assert build_config(VALID)["MAX_CONTENT_LENGTH"] == 1_048_576


def test_postgres_scheme_is_normalized():
    config = build_config({**VALID, "DATABASE_URL": "postgres://u:p@host/db"})
    assert config["SQLALCHEMY_DATABASE_URI"].startswith("postgresql://")


def test_clock_is_timezone_aware_and_replaceable():
    assert clock.utcnow().tzinfo is not None
    fixed = datetime(2026, 1, 1, tzinfo=timezone.utc)
    clock.set_clock(lambda: fixed)
    try:
        assert clock.utcnow() == fixed
    finally:
        clock.set_clock(None)
    clock.set_clock(lambda: datetime(2026, 1, 1))
    try:
        with pytest.raises(ValueError):
            clock.utcnow()
    finally:
        clock.set_clock(None)


@pytest.mark.parametrize("bad", [0, -1, -0.5, True, False, "1", None, float("nan"), float("inf"), 1e-400, [], {}])
def test_strict_number_rejects(bad):
    with pytest.raises(ValidationError):
        StrictNumber()._deserialize(bad, "order", {})


@pytest.mark.parametrize("good,expected", [(1, 1.0), (0.5, 0.5), (1e300, 1e300)])
def test_strict_number_accepts_positive_finite(good, expected):
    assert StrictNumber()._deserialize(good, "order", {}) == expected


def test_iso_uses_z_suffix():
    assert iso(datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)) == "2026-01-02T03:04:05Z"
    assert iso(None) is None


def test_password_hash_roundtrip():
    hashed = hash_password("correct horse")
    assert hashed.startswith("scrypt:32768:8:1$")
    assert verify_password(hashed, "correct horse")
    assert not verify_password(hashed, "wrong")
