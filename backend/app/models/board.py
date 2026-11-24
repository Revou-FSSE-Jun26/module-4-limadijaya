"""Board model."""

from app.extensions import db
from app.models import TimestampMixin, uuid_primary_key


class Board(TimestampMixin, db.Model):
    __tablename__ = "boards"

    id = uuid_primary_key()
    name = db.Column(db.Text, nullable=False)
