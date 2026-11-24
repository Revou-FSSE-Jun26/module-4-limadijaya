"""Card model."""

from app.extensions import db
from app.models import TimestampMixin, timestamp_column, uuid_primary_key


class Card(TimestampMixin, db.Model):
    __tablename__ = "cards"

    id = uuid_primary_key()
    column_id = db.Column(
        db.ForeignKey("columns.id", ondelete="CASCADE"),
        nullable=False,
    )
    title = db.Column(db.Text, nullable=False)
    position = db.Column(db.Float, nullable=False)
    assignee_id = db.Column(db.ForeignKey("users.id"), nullable=True)
    completed_at = timestamp_column(nullable=True)
    deleted_at = timestamp_column(nullable=True)
