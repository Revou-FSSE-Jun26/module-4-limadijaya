"""User account model."""

from app.extensions import db
from app.models import TimestampMixin, uuid_primary_key


class User(TimestampMixin, db.Model):
    __tablename__ = "users"

    id = uuid_primary_key()
    name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, nullable=False, unique=True)
    password_hash = db.Column(db.Text, nullable=False)
