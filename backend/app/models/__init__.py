"""Import every model so Flask-Migrate sees all eight tables."""
from .activity_event import ActivityEvent
from .board import Board
from .board_column import BoardColumn
from .board_membership import BoardMembership
from .card import Card
from .comment import Comment
from .notification import Notification
from .user import User

__all__ = [
    "ActivityEvent",
    "Board",
    "BoardColumn",
    "BoardMembership",
    "Card",
    "Comment",
    "Notification",
    "User",
]