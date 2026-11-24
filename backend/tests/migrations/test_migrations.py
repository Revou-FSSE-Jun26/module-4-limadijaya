"""Migration tests (NFR-009, DA-17, DA-14): upgrade, exact tables, RLS, drift, and downgrade cycle."""
import os

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from flask_migrate import downgrade, upgrade
from sqlalchemy import inspect, text

from app.extensions import db

MIGRATIONS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "migrations")
EIGHT = {
    "users", "boards", "board_memberships", "columns", "cards", "comments", "notifications", "activity_events",
}


def tables():
    return set(inspect(db.engine).get_table_names()) - {"alembic_version"}


def test_schema_has_exactly_the_eight_tables(app_context):
    assert tables() == EIGHT


def test_models_and_migration_have_no_drift(app_context):
    with db.engine.connect() as connection:
        diff = compare_metadata(MigrationContext.configure(connection), db.metadata)
    assert diff == [], diff


def test_row_level_security_is_enabled_without_policies(app_context):
    with db.engine.connect() as connection:
        enabled = {
            row[0]
            for row in connection.execute(
                text("SELECT relname FROM pg_class WHERE relrowsecurity AND relnamespace = 'public'::regnamespace")
            )
        }
        policies = connection.execute(text("SELECT count(*) FROM pg_policies WHERE schemaname = 'public'")).scalar()
    assert EIGHT <= enabled
    assert policies == 0


def test_position_columns_are_double_precision(app_context):
    columns = {t: {c["name"]: c for c in inspect(db.engine).get_columns(t)} for t in ("columns", "cards")}
    assert str(columns["cards"]["position"]["type"]) == "DOUBLE PRECISION"
    assert str(columns["columns"]["position"]["type"]) == "DOUBLE PRECISION"
    assert columns["cards"]["position"]["nullable"] is False
    assert columns["cards"]["deleted_at"]["nullable"] is True
    assert columns["columns"]["is_done"]["nullable"] is False


def test_downgrade_then_upgrade_cycle(app_context):
    db.session.remove()
    downgrade(directory=MIGRATIONS, revision="base")
    assert tables() == set()
    upgrade(directory=MIGRATIONS)
    assert tables() == EIGHT
