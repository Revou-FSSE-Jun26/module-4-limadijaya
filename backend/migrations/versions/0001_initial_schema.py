"""Initial schema: eight tables, constraints, partial indexes, cascades, and RLS.

Revision ID: 0001_initial
Revises:
Create Date: 2026-11-24

Hand-reviewed after autogenerate (DB-15): partial indexes, CHECK constraints and the
ON DELETE CASCADE chain of DA-14 are written explicitly. Only board_id cascades on
notifications and activity_events (DB-09).
"""
import sqlalchemy as sa
from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

TABLES = (
    "users",
    "boards",
    "board_memberships",
    "columns",
    "cards",
    "comments",
    "notifications",
    "activity_events",
)


def _uuid_pk():
    return sa.Column("id", sa.Uuid(), primary_key=True, nullable=False)


def _ts(name, nullable=False):
    return sa.Column(name, sa.DateTime(timezone=True), nullable=nullable)


def upgrade():
    op.create_table(
        "users",
        _uuid_pk(),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        _ts("created_at"),
        _ts("updated_at"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_table(
        "boards",
        _uuid_pk(),
        sa.Column("name", sa.Text(), nullable=False),
        _ts("created_at"),
        _ts("updated_at"),
    )
    op.create_table(
        "board_memberships",
        _uuid_pk(),
        sa.Column("board_id", sa.Uuid(), sa.ForeignKey("boards.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        _ts("created_at"),
        sa.UniqueConstraint("board_id", "user_id", name="uq_membership_board_user"),
        sa.CheckConstraint("role IN ('administrator','member')", name="ck_membership_role"),
    )
    op.create_index("ix_board_memberships_user_id", "board_memberships", ["user_id"])

    op.create_table(
        "columns",
        _uuid_pk(),
        sa.Column("board_id", sa.Uuid(), sa.ForeignKey("boards.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("position", sa.Float(), nullable=False),
        sa.Column("is_done", sa.Boolean(), nullable=False, server_default=sa.false()),
        _ts("deleted_at", nullable=True),
        _ts("created_at"),
        _ts("updated_at"),
    )
    op.create_index(
        "ix_columns_board_live", "columns", ["board_id", "position"], postgresql_where=sa.text("deleted_at IS NULL")
    )

    op.create_table(
        "cards",
        _uuid_pk(),
        sa.Column("column_id", sa.Uuid(), sa.ForeignKey("columns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("position", sa.Float(), nullable=False),
        sa.Column("assignee_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        _ts("completed_at", nullable=True),
        _ts("deleted_at", nullable=True),
        _ts("created_at"),
        _ts("updated_at"),
    )
    op.create_index(
        "ix_cards_column_live", "cards", ["column_id", "position"], postgresql_where=sa.text("deleted_at IS NULL")
    )
    op.create_index(
        "ix_cards_assignee_live", "cards", ["assignee_id"], postgresql_where=sa.text("deleted_at IS NULL")
    )
    op.create_index(
        "ix_cards_completed_live",
        "cards",
        ["column_id", "completed_at"],
        postgresql_where=sa.text("deleted_at IS NULL AND completed_at IS NOT NULL"),
    )

    op.create_table(
        "comments",
        _uuid_pk(),
        sa.Column("card_id", sa.Uuid(), sa.ForeignKey("cards.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        _ts("created_at"),
        _ts("updated_at"),
    )
    op.create_index("ix_comments_card_created", "comments", ["card_id", "created_at"])

    op.create_table(
        "notifications",
        _uuid_pk(),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("board_id", sa.Uuid(), sa.ForeignKey("boards.id", ondelete="CASCADE"), nullable=False),
        sa.Column("card_id", sa.Uuid(), sa.ForeignKey("cards.id"), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        _ts("created_at"),
        sa.CheckConstraint("type IN ('card_assigned','comment_added')", name="ck_notifications_type"),
    )
    op.create_index(
        "ix_notifications_user_created",
        "notifications",
        ["user_id", sa.text("created_at DESC"), sa.text("id DESC")],
    )

    op.create_table(
        "activity_events",
        _uuid_pk(),
        sa.Column("board_id", sa.Uuid(), sa.ForeignKey("boards.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("card_id", sa.Uuid(), sa.ForeignKey("cards.id"), nullable=False),
        sa.Column("comment_id", sa.Uuid(), nullable=True),  # no foreign key (DA-14)
        sa.Column("from_column_id", sa.Uuid(), sa.ForeignKey("columns.id"), nullable=True),
        sa.Column("to_column_id", sa.Uuid(), sa.ForeignKey("columns.id"), nullable=True),
        _ts("created_at"),
        sa.CheckConstraint("type IN ('card_created','card_moved','comment_created')", name="ck_events_type"),
        sa.CheckConstraint(
            "type <> 'card_moved' OR (from_column_id IS NOT NULL AND to_column_id IS NOT NULL)",
            name="ck_events_moved_columns",
        ),
    )
    op.create_index("ix_events_board_actor_created", "activity_events", ["board_id", "created_at", "actor_id"])

    # DA-17: Row Level Security on every application table, with no policy for browser-facing roles.
    # The Flask database role owns the tables and is not subject to RLS.
    for table in TABLES:
        op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')


def downgrade():
    for table in reversed(TABLES):
        op.execute(f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY')
    op.drop_table("activity_events")
    op.drop_table("notifications")
    op.drop_table("comments")
    op.drop_table("cards")
    op.drop_table("columns")
    op.drop_table("board_memberships")
    op.drop_table("boards")
    op.drop_table("users")
