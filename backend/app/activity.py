"""Activity events and notifications are written by the acting service in the same transaction (BE-14)."""
from __future__ import annotations

from .access import get_membership
from .extensions import db
from .models import ActivityEvent, Notification
from .models.activity_event import EVENT_CARD_CREATED, EVENT_CARD_MOVED, EVENT_COMMENT_CREATED


def record_event(board_id, actor_id, event_type, card_id, now, comment_id=None, from_column_id=None, to_column_id=None):
    db.session.add(
        ActivityEvent(
            board_id=board_id,
            actor_id=actor_id,
            type=event_type,
            card_id=card_id,
            comment_id=comment_id,
            from_column_id=from_column_id,
            to_column_id=to_column_id,
            created_at=now,
        )
    )


def notify(recipient_id, actor, board_id, card, notification_type, message, now) -> bool:
    """Create a notification only for a current member of the card's board (NOTIF-003-AC15)."""
    if get_membership(recipient_id, board_id) is None:
        return False
    db.session.add(
        Notification(
            user_id=recipient_id,
            actor_id=actor.id,
            board_id=board_id,
            card_id=card.id,
            type=notification_type,
            message=message,
            is_read=False,
            created_at=now,
        )
    )
    return True


__all__ = ["record_event", "notify", "EVENT_CARD_CREATED", "EVENT_CARD_MOVED", "EVENT_COMMENT_CREATED"]