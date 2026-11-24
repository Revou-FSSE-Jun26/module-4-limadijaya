"""Shared SQLAlchemy model helpers."""

from __future__ import annotations

import uuid

from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db


def uuid_primary_key():
    """Return the approved UUID primary-key column definition."""

    return db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        default=uuid.uuid4,
    )


def timestamp_column(*, nullable: bool = False):
    """Return a timezone-aware timestamp column set explicitly by services."""

    return db.Column(db.DateTime(timezone=True), nullable=nullable)


class TimestampMixin:
    """Common timestamp fields for entities that have created/updated times."""

    created_at = timestamp_column()
    updated_at = timestamp_column()


from app.models.activity_event import ActivityEvent
from app.models.board import Board
from app.models.board_column import BoardColumn
from app.models.board_membership import BoardMembership
from app.models.card import Card
from app.models.comment import Comment
from app.models.notification import Notification
from app.models.user import User


__all__ = [
    "ActivityEvent",
    "Board",
    "BoardColumn",
    "BoardMembership",
    "Card",
    "Comment",
    "Notification",
    "TimestampMixin",
    "User",
    "db",
    "timestamp_column",
    "uuid_primary_key",
]
