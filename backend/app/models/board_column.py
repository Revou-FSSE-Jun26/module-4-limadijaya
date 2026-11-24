"""Board column model."""

from app.extensions import db
from app.models import TimestampMixin, timestamp_column, uuid_primary_key


class BoardColumn(TimestampMixin, db.Model):
    __tablename__ = "columns"

    id = uuid_primary_key()
    board_id = db.Column(
        db.ForeignKey("boards.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = db.Column(db.Text, nullable=False)
    position = db.Column(db.Float, nullable=False)
    is_done = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        server_default=db.false(),
    )
    deleted_at = timestamp_column(nullable=True)
