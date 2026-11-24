"""Production-safety guard for the backend test session (T1.04).

This module only decides whether a test session may start. It refuses to run
unless TEST_DATABASE_URL names the approved local test database, and unless the
production URL (DATABASE_URL) cannot be the same database. It never opens a
database connection, and its error messages never contain a URL, a host, or a
password. Fixtures (application, client, database, clock) belong to T2.09.

The approved destination is the local PostgreSQL test database prepared for
this project (README.md, "Local development setup"). Change the constants below
only with human approval.
"""
from __future__ import annotations

import os
from collections.abc import Mapping
from urllib.parse import parse_qs, unquote, urlsplit

import pytest

TEST_URL_VARIABLE = "TEST_DATABASE_URL"
PRODUCTION_URL_VARIABLE = "DATABASE_URL"

APPROVED_SCHEMES = frozenset({"postgresql", "postgresql+psycopg2"})
APPROVED_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})
APPROVED_PORT = 5432
APPROVED_DATABASE = "revotask_test"
APPROVED_USER = "revotask_test_user"

# libpq reads these when a URL does not set the part itself. PGHOSTADDR and the
# service variables can redirect a connection even when the URL host looks local,
# so the session is refused whenever any of them is set.
FORBIDDEN_LIBPQ_VARIABLES = (
    "PGHOST",
    "PGHOSTADDR",
    "PGPORT",
    "PGDATABASE",
    "PGUSER",
    "PGSERVICE",
    "PGSERVICEFILE",
)


class UnsafeTestDatabaseError(Exception):
    """The test database settings are missing, malformed, or unsafe."""


def _refuse(reason: str) -> UnsafeTestDatabaseError:
    return UnsafeTestDatabaseError(f"Refusing to run tests: {reason}")


def _has_unsafe_characters(value: str) -> bool:
    # Control characters, spaces, DEL, and non-ASCII characters are never valid here.
    return any(ord(ch) < 33 or ord(ch) > 126 for ch in value)


def _validate_test_url(url: str) -> None:
    """Raise UnsafeTestDatabaseError unless url is exactly the approved local destination."""
    if url == "":
        raise _refuse(f"{TEST_URL_VARIABLE} is set but empty.")
    if _has_unsafe_characters(url):
        raise _refuse(f"{TEST_URL_VARIABLE} is malformed (it contains spaces or control characters).")
    if "?" in url or "#" in url:
        raise _refuse(f"{TEST_URL_VARIABLE} must not contain a query string or a fragment, "
                      "because connection parameters could override the approved destination.")
    if url.count("@") != 1:
        raise _refuse(f"{TEST_URL_VARIABLE} is malformed or ambiguous (it must contain exactly one '@').")

    try:
        parts = urlsplit(url)
        host = parts.hostname
        port = parts.port
    except ValueError:
        raise _refuse(f"{TEST_URL_VARIABLE} is malformed.") from None

    if parts.scheme not in APPROVED_SCHEMES:
        raise _refuse(f"{TEST_URL_VARIABLE} must use the postgresql scheme.")

    userinfo = parts.netloc.rpartition("@")[0]
    if userinfo.count(":") > 1:
        raise _refuse(f"{TEST_URL_VARIABLE} is ambiguous (percent-encode special characters in the password).")
    if parts.username != APPROVED_USER:
        raise _refuse(f"{TEST_URL_VARIABLE} must use the dedicated test role {APPROVED_USER}.")

    if host is None or host not in APPROVED_HOSTS:
        raise _refuse(f"{TEST_URL_VARIABLE} must point to the local machine "
                      "(localhost, 127.0.0.1, or ::1). Remote databases are never allowed.")
    if (port if port is not None else APPROVED_PORT) != APPROVED_PORT:
        raise _refuse(f"{TEST_URL_VARIABLE} must use port {APPROVED_PORT}.")
    if parts.path != f"/{APPROVED_DATABASE}":
        raise _refuse(f"{TEST_URL_VARIABLE} must name the dedicated test database {APPROVED_DATABASE}.")


def _points_at_approved_destination(url: str) -> bool:
    """True if url could connect to the approved local test destination.

    Any host, port, or database given in the path or in query parameters counts,
    so an equivalent URL (another alias, a default port, a host= override) is
    detected. Raises ValueError when url cannot be analysed.
    """
    parts = urlsplit(url.strip())
    query = parse_qs(parts.query, keep_blank_values=True)

    hosts = {(parts.hostname or "").lower()}
    hosts.update(value.lower() for key in ("host", "hostaddr") for value in query.get(key, []))
    ports = {parts.port if parts.port is not None else APPROVED_PORT}
    ports.update(int(value) for value in query.get("port", []) if value != "")
    databases = {unquote(parts.path.lstrip("/")).lower()}
    databases.update(unquote(value).lower() for value in query.get("dbname", []))

    return bool(hosts & APPROVED_HOSTS) and APPROVED_PORT in ports and APPROVED_DATABASE in databases


def check_test_database_environment(environ: Mapping[str, str]) -> None:
    """Validate the test database settings. Raise UnsafeTestDatabaseError if unsafe.

    Pure function: reads only the given mapping and never connects to a database.
    """
    test_url = environ.get(TEST_URL_VARIABLE)
    if test_url is None:
        raise _refuse(f"{TEST_URL_VARIABLE} is not set. See README.md, 'Local development setup'.")

    _validate_test_url(test_url)

    present = [name for name in FORBIDDEN_LIBPQ_VARIABLES if environ.get(name)]
    if present:
        raise _refuse("PostgreSQL connection environment variables are set ("
                      + ", ".join(present) + "). They could redirect the test connection. Unset them.")

    production_url = environ.get(PRODUCTION_URL_VARIABLE)
    if production_url is not None and production_url.strip() != "":
        if production_url.strip() == test_url.strip():
            raise _refuse(f"{TEST_URL_VARIABLE} equals {PRODUCTION_URL_VARIABLE}. "
                          "Tests must not use the production database.")
        try:
            same_destination = _points_at_approved_destination(production_url)
        except ValueError:
            raise _refuse(f"{PRODUCTION_URL_VARIABLE} could not be analysed, so it cannot be shown "
                          f"to differ from {TEST_URL_VARIABLE}.") from None
        if same_destination:
            raise _refuse(f"{PRODUCTION_URL_VARIABLE} points at the same database as "
                          f"{TEST_URL_VARIABLE}. Tests must not use the production database.")


def validated_test_database_url(environ: Mapping[str, str] | None = None) -> str:
    """Return the test database URL after the guard has passed (for T2.09 and later)."""
    env = os.environ if environ is None else environ
    check_test_database_environment(env)
    return env[TEST_URL_VARIABLE]


def pytest_configure(config: pytest.Config) -> None:
    """Run the guard before collection and before any test or fixture can connect."""
    try:
        check_test_database_environment(os.environ)
    except UnsafeTestDatabaseError as exc:
        raise pytest.UsageError(str(exc)) from None
    except Exception:  # fail closed on anything unexpected, without echoing details
        raise pytest.UsageError(
            "Refusing to run tests: the test database settings could not be validated."
        ) from None
