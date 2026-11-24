from ..extensions import db
from ._base import timestamp, uuid_pk


class Board(db.Model):
    __tablename__ = "boards"

    id = uuid_pk()
    name = db.Column(db.Text, nullable=False)
    created_at = timestamp()
    updated_at = timestamp()