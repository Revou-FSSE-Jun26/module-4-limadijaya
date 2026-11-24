from ..extensions import db
from ._base import timestamp, uuid_pk


class User(db.Model):
    __tablename__ = "users"

    id = uuid_pk()
    name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, nullable=False, unique=True)
    password_hash = db.Column(db.Text, nullable=False)
    created_at = timestamp()
    updated_at = timestamp()