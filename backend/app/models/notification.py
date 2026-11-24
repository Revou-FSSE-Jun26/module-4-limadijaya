"""Notification model."""

from app.extensions import db
from app.models import timestamp_column, uuid_primary_key


class Notification(db.Model):
    __tablename__ = "notifications"
    __table_args__ = (
        db.CheckConstraint(
            "type IN ('card_assigned', 'comment_added')",
            name="ck_notifications_type",
        ),
    )

    id = uuid_primary_key()
    user_id = db.Column(db.ForeignKey("users.id"), nullable=False)
    actor_id = db.Column(db.ForeignKey("users.id"), nullable=False)
    board_id = db.Column(
        db.ForeignKey("boards.id", ondelete="CASCADE"),
        nullable=False,
    )
    card_id = db.Column(db.ForeignKey("cards.id"), nullable=False)
    type = db.Column(db.Text, nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        server_default=db.false(),
    )
    created_at = timestamp_column()
