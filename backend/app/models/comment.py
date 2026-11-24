from ..extensions import db
from ._base import timestamp, uuid_fk, uuid_pk


class Comment(db.Model):
    """Hard-deleted (DB-06). No deleted_at column."""

    __tablename__ = "comments"
    __table_args__ = (db.Index("ix_comments_card_created", "card_id", "created_at"),)

    id = uuid_pk()
    card_id = uuid_fk("cards.id", ondelete="CASCADE")
    author_id = uuid_fk("users.id")
    content = db.Column(db.Text, nullable=False)
    created_at = timestamp()
    updated_at = timestamp()