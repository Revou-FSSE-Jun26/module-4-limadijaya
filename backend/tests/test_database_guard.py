"""Unit tests for the test-session safety guard in conftest.py (T1.04).

All credentials and hosts here are synthetic. Nothing connects to a database:
the guard is a pure function over a mapping, and the subprocess tests only start
pytest in collect-only mode. The tests pass isolated mappings to the guard, so
they do not depend on the real environment, except for the startup guard itself,
which needs a safe synthetic TEST_DATABASE_URL (see README.md).
"""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]

# Load the guard under a private name so these tests never depend on how pytest
# imported conftest.py.
_spec = importlib.util.spec_from_file_location("revotask_database_guard", Path(__file__).with_name("conftest.py"))
guard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(guard)

USER = "revotask_test_user"
PASSWORD = "SyntheticPw123"
PROD_PASSWORD = "SyntheticProdPw456"
GOOD = f"postgresql://{USER}:{PASSWORD}@localhost:5432/revotask_test"
REMOTE_PROD = f"postgresql://prod_user:{PROD_PASSWORD}@db.example.invalid:5432/postgres"

# Text that must never appear in an error message.
FORBIDDEN_IN_MESSAGES = (
    PASSWORD,
    PROD_PASSWORD,
    "evil.example",
    "db.example.invalid",
    "prod_user",
    "postgresql://",
    "postgres://",
)


def make_env(test=None, prod=None, **extra):
    env = {}
    if test is not None:
        env["TEST_DATABASE_URL"] = test
    if prod is not None:
        env["DATABASE_URL"] = prod
    env.update(extra)
    return env


def refusal_message(env):
    with pytest.raises(guard.UnsafeTestDatabaseError) as info:
        guard.check_test_database_environment(env)
    return str(info.value)


def assert_safe_message(message, env):
    assert message.startswith("Refusing to run tests: ")
    for text in FORBIDDEN_IN_MESSAGES:
        assert text not in message
    for value in env.values():  # no configured value is echoed back
        if len(value) >= 8:
            assert value not in message


def url(host="localhost", port="5432", database="revotask_test", user=USER, scheme="postgresql"):
    return f"{scheme}://{user}:{PASSWORD}@{host}:{port}/{database}" if port else f"{scheme}://{user}:{PASSWORD}@{host}/{database}"


# --------------------------------------------------------------------------- accepted

ACCEPTED_TEST_URLS = [
    pytest.param(GOOD, id="approved-local-url"),
    pytest.param(url(host="127.0.0.1"), id="ipv4-loopback"),
    pytest.param(url(host="[::1]"), id="ipv6-loopback"),
    pytest.param(url(host="LOCALHOST"), id="uppercase-localhost"),
    pytest.param(url(port=""), id="port-omitted-defaults-to-5432"),
    pytest.param(url(scheme="postgresql+psycopg2"), id="psycopg2-scheme"),
    pytest.param(f"postgresql://{USER}@localhost:5432/revotask_test", id="no-password"),
]


@pytest.mark.parametrize("test_url", ACCEPTED_TEST_URLS)
def test_accepts_approved_local_test_urls(test_url):
    guard.check_test_database_environment(make_env(test_url))


def test_accepts_a_different_remote_production_url():
    guard.check_test_database_environment(make_env(GOOD, REMOTE_PROD))


@pytest.mark.parametrize("blank", ["", "   "])
def test_blank_production_url_is_treated_as_unset(blank):
    guard.check_test_database_environment(make_env(GOOD, blank))


def test_validated_test_database_url_returns_the_url_after_the_guard_passes():
    assert guard.validated_test_database_url(make_env(GOOD)) == GOOD


def test_validated_test_database_url_refuses_when_unsafe():
    with pytest.raises(guard.UnsafeTestDatabaseError):
        guard.validated_test_database_url(make_env())


# --------------------------------------------------------------------------- missing and malformed

MISSING_OR_MALFORMED = [
    pytest.param("", id="empty"),
    pytest.param("   ", id="whitespace-only"),
    pytest.param(GOOD + " ", id="trailing-space"),
    pytest.param(" " + GOOD, id="leading-space"),
    pytest.param(GOOD + "\nPGHOST=evil.example", id="embedded-newline"),
    pytest.param(GOOD.replace("localhost", "local\thost"), id="embedded-tab"),
    pytest.param(GOOD.replace("localhost", "locaIhost\u00e9"), id="non-ascii"),
    pytest.param("localhost revotask_test", id="not-a-url"),
    pytest.param(url(port="abc"), id="non-numeric-port"),
    pytest.param(url(port="99999"), id="port-out-of-range"),
    pytest.param("sqlite:///test.db", id="sqlite-scheme"),
    pytest.param(url(scheme="postgres"), id="postgres-scheme"),
    pytest.param(url(scheme="mysql"), id="mysql-scheme"),
]


def test_refuses_when_test_url_is_missing():
    env = make_env()
    assert_safe_message(refusal_message(env), env)
    assert "TEST_DATABASE_URL is not set" in refusal_message(env)


@pytest.mark.parametrize("test_url", MISSING_OR_MALFORMED)
def test_refuses_empty_and_malformed_test_urls(test_url):
    env = make_env(test_url)
    assert_safe_message(refusal_message(env), env)


# --------------------------------------------------------------------------- remote destinations

REMOTE_OR_LOOKALIKE_HOSTS = [
    pytest.param(url(host="evil.example"), id="remote-host"),
    pytest.param(url(host="db.example.invalid"), id="hosted-database-style-host"),
    pytest.param(url(host="localhost."), id="trailing-dot"),
    pytest.param(url(host="localhost.evil.example"), id="suffix-trick"),
    pytest.param(url(host="evil-localhost"), id="prefix-trick"),
    pytest.param(url(host="127.0.0.2"), id="other-loopback-address"),
    pytest.param(url(host="0.0.0.0"), id="unspecified-address"),
    pytest.param(f"postgresql://{USER}:{PASSWORD}@/revotask_test", id="no-host-unix-socket"),
    pytest.param(url(host="%6Cocalhost"), id="percent-encoded-host"),
    pytest.param(url(host="localhost:5432,evil.example"), id="multi-host-list"),
    pytest.param(f"postgresql://{USER}:{PASSWORD}@evil.example@localhost:5432/revotask_test", id="double-at-sign"),
    pytest.param("postgresql://localhost:5432/revotask_test", id="no-userinfo"),
]


@pytest.mark.parametrize("test_url", REMOTE_OR_LOOKALIKE_HOSTS)
def test_refuses_remote_and_lookalike_hosts(test_url):
    env = make_env(test_url)
    assert_safe_message(refusal_message(env), env)


# --------------------------------------------------------------------------- wrong port, database, role

WRONG_DESTINATION_PARTS = [
    pytest.param(url(port="5433"), id="port-5433"),
    pytest.param(url(port="6543"), id="port-6543"),
    pytest.param(url(database="postgres"), id="database-postgres"),
    pytest.param(url(database="revotask"), id="database-revotask"),
    pytest.param(url(database="revotask_test2"), id="database-suffix"),
    pytest.param(url(database="REVOTASK_TEST"), id="database-uppercase"),
    pytest.param(url(database="revotask%5Ftest"), id="database-percent-encoded"),
    pytest.param(GOOD + "/", id="trailing-slash"),
    pytest.param(GOOD + "/extra", id="extra-path-segment"),
    pytest.param(f"postgresql://{USER}:{PASSWORD}@localhost:5432", id="no-database"),
    pytest.param(url(user="postgres"), id="role-postgres-superuser"),
    pytest.param(url(user="someone"), id="role-other"),
    pytest.param(url(user="revotask%5Ftest_user"), id="role-percent-encoded"),
    pytest.param(f"postgresql://{USER}:Synthetic:Pw@localhost:5432/revotask_test", id="password-with-extra-colon"),
]


@pytest.mark.parametrize("test_url", WRONG_DESTINATION_PARTS)
def test_refuses_wrong_port_database_or_role(test_url):
    env = make_env(test_url)
    assert_safe_message(refusal_message(env), env)


# --------------------------------------------------------------------------- connection parameter overrides

OVERRIDE_QUERIES = [
    "host=evil.example",
    "hostaddr=203.0.113.9",
    "port=5433",
    "dbname=postgres",
    "service=prod",
    "sslmode=disable",
    "options=-csearch_path%3Dpublic",
    "target_session_attrs=any",
    "",
]


@pytest.mark.parametrize("query", OVERRIDE_QUERIES, ids=[q or "empty-query" for q in OVERRIDE_QUERIES])
def test_refuses_any_query_string_on_the_test_url(query):
    env = make_env(GOOD + "?" + query)
    assert_safe_message(refusal_message(env), env)


def test_refuses_a_fragment_on_the_test_url():
    env = make_env(GOOD + "#fragment")
    assert_safe_message(refusal_message(env), env)


# --------------------------------------------------------------------------- production URL reuse

PRODUCTION_URLS_THAT_ARE_THE_TEST_DATABASE = [
    pytest.param(GOOD, id="identical"),
    pytest.param("  " + GOOD + "  ", id="identical-with-padding"),
    pytest.param(f"postgresql://{USER}:OtherSynthetic@localhost:5432/revotask_test", id="same-database-other-password"),
    pytest.param("postgresql://u:p@127.0.0.1:5432/revotask_test", id="ipv4-alias"),
    pytest.param("postgresql://u:p@[::1]:5432/revotask_test", id="ipv6-alias"),
    pytest.param("postgresql://u:p@localhost/revotask_test", id="default-port"),
    pytest.param("postgresql://u:p@LOCALHOST:5432/REVOTASK_TEST", id="uppercase"),
    pytest.param("postgresql+psycopg2://u:p@localhost:5432/revotask_test", id="psycopg2-scheme"),
    pytest.param("postgres://u:p@localhost:5432/revotask_test", id="postgres-scheme"),
    pytest.param("postgresql://u:p@localhost:5432/revotask%5Ftest", id="percent-encoded-database"),
    pytest.param("postgresql://u:p@db.example.invalid:5432/revotask_test?host=localhost", id="host-override"),
    pytest.param("postgresql://u:p@db.example.invalid/revotask_test?hostaddr=127.0.0.1", id="hostaddr-override"),
    pytest.param("postgresql://u:p@localhost/other?dbname=revotask_test", id="dbname-override"),
    pytest.param("postgresql://u:p@localhost:6543/revotask_test?port=5432", id="port-override"),
]


@pytest.mark.parametrize("production_url", PRODUCTION_URLS_THAT_ARE_THE_TEST_DATABASE)
def test_refuses_identical_or_equivalent_production_url(production_url):
    env = make_env(GOOD, production_url)
    assert_safe_message(refusal_message(env), env)


@pytest.mark.parametrize(
    "production_url",
    [
        pytest.param("postgresql://u:p@localhost:abc/revotask_test", id="non-numeric-port"),
        pytest.param("postgresql://u:p@localhost/x?port=abc", id="non-numeric-port-parameter"),
    ],
)
def test_refuses_when_the_production_url_cannot_be_analysed(production_url):
    env = make_env(GOOD, production_url)
    assert_safe_message(refusal_message(env), env)


# --------------------------------------------------------------------------- PostgreSQL environment variables

LIBPQ_VARIABLES = ["PGHOST", "PGHOSTADDR", "PGPORT", "PGDATABASE", "PGUSER", "PGSERVICE", "PGSERVICEFILE"]


@pytest.mark.parametrize("name", LIBPQ_VARIABLES)
def test_refuses_when_a_destination_libpq_variable_is_set(name):
    env = make_env(GOOD, **{name: "evil.example"})
    message = refusal_message(env)
    assert_safe_message(message, env)
    assert name in message  # the variable NAME is reported, never its value


@pytest.mark.parametrize("name", LIBPQ_VARIABLES)
def test_ignores_an_empty_libpq_variable(name):
    guard.check_test_database_environment(make_env(GOOD, **{name: ""}))


def test_unrelated_libpq_password_variable_does_not_block():
    guard.check_test_database_environment(make_env(GOOD, PGPASSWORD=PASSWORD))


# --------------------------------------------------------------------------- credential leakage and fail-closed hook

def test_error_messages_never_contain_credentials_hosts_or_urls():
    unsafe_environments = [
        make_env(url(host="evil.example")),
        make_env(url(user="postgres")),
        make_env(GOOD, GOOD),
        make_env(GOOD, REMOTE_PROD.replace("db.example.invalid", "localhost").replace("/postgres", "/revotask_test")),
        make_env(GOOD, PGHOST="evil.example"),
        make_env(GOOD + "?host=evil.example"),
    ]
    for env in unsafe_environments:
        assert_safe_message(refusal_message(env), env)


def test_pytest_configure_raises_a_usage_error_for_an_unsafe_environment(monkeypatch):
    monkeypatch.delenv("TEST_DATABASE_URL", raising=False)
    with pytest.raises(pytest.UsageError) as info:
        guard.pytest_configure(None)
    assert str(info.value).startswith("Refusing to run tests: ")


def test_pytest_configure_accepts_a_safe_environment(monkeypatch):
    monkeypatch.setenv("TEST_DATABASE_URL", GOOD)
    for name in ("DATABASE_URL", *LIBPQ_VARIABLES):
        monkeypatch.delenv(name, raising=False)
    guard.pytest_configure(None)


def test_pytest_configure_fails_closed_without_echoing_unexpected_errors(monkeypatch):
    def explode(environ):
        raise RuntimeError(f"unexpected failure containing {PASSWORD}")

    monkeypatch.setattr(guard, "check_test_database_environment", explode)
    with pytest.raises(pytest.UsageError) as info:
        guard.pytest_configure(None)
    message = str(info.value)
    assert message.startswith("Refusing to run tests: ")
    assert PASSWORD not in message
    assert "unexpected failure" not in message


# --------------------------------------------------------------------------- real pytest startup (collect-only, no tests run, no connection)

def run_pytest_startup(**variables):
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in ("TEST_DATABASE_URL", "DATABASE_URL") and not key.startswith("PG")
    }
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["REVOTASK_NO_DOTENV"] = "1"  # a local backend/.env must not refill the removed variables
    env.update(variables)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "--collect-only", "-q",
         "tests/test_database_guard.py"],
        cwd=BACKEND_DIR, env=env, capture_output=True, text=True, timeout=180,
    )
    return result.returncode, result.stdout + result.stderr


@pytest.mark.parametrize(
    "variables",
    [
        pytest.param({}, id="test-url-missing"),
        pytest.param({"TEST_DATABASE_URL": url(host="evil.example")}, id="remote-host"),
        pytest.param({"TEST_DATABASE_URL": GOOD, "DATABASE_URL": GOOD}, id="production-url-identical"),
        pytest.param({"TEST_DATABASE_URL": GOOD, "PGHOST": "evil.example"}, id="libpq-override"),
        pytest.param({"TEST_DATABASE_URL": GOOD + "?host=evil.example"}, id="query-override"),
    ],
)
def test_pytest_startup_fails_closed_for_unsafe_settings(variables):
    returncode, output = run_pytest_startup(**variables)
    assert returncode == 4
    assert "Refusing to run tests" in output
    assert "Traceback" not in output
    for text in FORBIDDEN_IN_MESSAGES:
        assert text not in output


def test_pytest_startup_succeeds_for_a_safe_synthetic_url():
    returncode, output = run_pytest_startup(TEST_DATABASE_URL=GOOD, DATABASE_URL=REMOTE_PROD)
    assert returncode == 0
    assert "Refusing to run tests" not in output
