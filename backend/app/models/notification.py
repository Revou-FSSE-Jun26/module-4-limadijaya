from ..extensions import db
from ._base import timestamp, uuid_fk, uuid_pk

TYPE_CARD_ASSIGNED = "card_assigned"
TYPE_COMMENT_ADDED = "comment_added"


class Notification(db.Model):
    __tablename__ = "notifications"
    __table_args__ = (
        db.CheckConstraint("type IN ('card_assigned','comment_added')", name="ck_notifications_type"),
        db.Index("ix_notifications_user_created", "user_id", db.text("created_at DESC"), db.text("id DESC")),
    )

    id = uuid_pk()
    user_id = uuid_fk("users.id")
    actor_id = uuid_fk("users.id")
    board_id = uuid_fk("boards.id", ondelete="CASCADE")
    card_id = uuid_fk("cards.id")
    type = db.Column(db.Text, nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())
    created_at = timestamp()