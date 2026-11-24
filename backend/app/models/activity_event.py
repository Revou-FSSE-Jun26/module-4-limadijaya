"""Append-only activity event model."""

from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db
from app.models import timestamp_column, uuid_primary_key


class ActivityEvent(db.Model):
    __tablename__ = "activity_events"
    __table_args__ = (
        db.CheckConstraint(
            "type IN ('card_created', 'card_moved', 'comment_created')",
            name="ck_activity_events_type",
        ),
        db.CheckConstraint(
            "type <> 'card_moved' OR "
            "(from_column_id IS NOT NULL AND to_column_id IS NOT NULL)",
            name="ck_activity_events_move_columns",
        ),
    )

    id = uuid_primary_key()
    board_id = db.Column(
        db.ForeignKey("boards.id", ondelete="CASCADE"),
        nullable=False,
    )
    actor_id = db.Column(db.ForeignKey("users.id"), nullable=False)
    type = db.Column(db.Text, nullable=False)
    card_id = db.Column(db.ForeignKey("cards.id"), nullable=False)
    comment_id = db.Column(UUID(as_uuid=True), nullable=True)
    from_column_id = db.Column(db.ForeignKey("columns.id"), nullable=True)
    to_column_id = db.Column(db.ForeignKey("columns.id"), nullable=True)
    created_at = timestamp_column()
