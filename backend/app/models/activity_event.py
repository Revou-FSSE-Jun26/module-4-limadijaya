from ..extensions import db
from ._base import timestamp, uuid_fk, uuid_pk
from sqlalchemy import Uuid

EVENT_CARD_CREATED = "card_created"
EVENT_CARD_MOVED = "card_moved"
EVENT_COMMENT_CREATED = "comment_created"


class ActivityEvent(db.Model):
    """Append-only (DB-09). Only board_id cascades. comment_id has no foreign key (DA-14)."""

    __tablename__ = "activity_events"
    __table_args__ = (
        db.CheckConstraint(
            "type IN ('card_created','card_moved','comment_created')", name="ck_events_type"
        ),
        db.CheckConstraint(
            "type <> 'card_moved' OR (from_column_id IS NOT NULL AND to_column_id IS NOT NULL)",
            name="ck_events_moved_columns",
        ),
        db.Index("ix_events_board_actor_created", "board_id", "created_at", "actor_id"),
    )

    id = uuid_pk()
    board_id = uuid_fk("boards.id", ondelete="CASCADE")
    actor_id = uuid_fk("users.id")
    type = db.Column(db.Text, nullable=False)
    card_id = uuid_fk("cards.id")
    comment_id = db.Column(Uuid(as_uuid=True), nullable=True)
    from_column_id = uuid_fk("columns.id", nullable=True)
    to_column_id = uuid_fk("columns.id", nullable=True)
    created_at = timestamp()