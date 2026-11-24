"""Comment model."""

from app.extensions import db
from app.models import TimestampMixin, uuid_primary_key


class Comment(TimestampMixin, db.Model):
    __tablename__ = "comments"

    id = uuid_primary_key()
    card_id = db.Column(
        db.ForeignKey("cards.id", ondelete="CASCADE"),
        nullable=False,
    )
    author_id = db.Column(db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
