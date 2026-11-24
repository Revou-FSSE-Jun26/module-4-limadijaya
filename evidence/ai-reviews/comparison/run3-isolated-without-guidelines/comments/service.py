import uuid
from datetime import datetime, timezone

from app.extensions import db
from app.models import (
    ActivityEvent,
    BoardColumn,
    BoardMembership,
    Card,
    Comment,
    Notification,
    User,
)


class ServiceError(Exception):
    def __init__(self, message, status):
        super().__init__(message)
        self.message = message
        self.status = status


def _uuid(value):
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except (ValueError, AttributeError, TypeError):
        raise ServiceError("not found", 404)


def _iso(value):
    return value.isoformat() if value is not None else None


def serialize(comment, author=None):
    if author is None:
        author = db.session.get(User, comment.author_id)
    return {
        "id": str(comment.id),
        "card_id": str(comment.card_id),
        "content": comment.content,
        "author": {
            "id": str(comment.author_id),
            "name": author.name if author else None,
        },
        "created_at": _iso(comment.created_at),
        "updated_at": _iso(comment.updated_at),
    }


def _board_id_for_card(card_id, user_id):
    """Return (card, board_id) if the card is live and user is a member, else 404."""
    card = db.session.get(Card, _uuid(card_id))
    if card is None or card.deleted_at is not None:
        raise ServiceError("card not found", 404)
    column = db.session.get(BoardColumn, card.column_id)
    if column is None or column.deleted_at is not None:
        raise ServiceError("card not found", 404)
    membership = BoardMembership.query.filter_by(
        board_id=column.board_id, user_id=user_id
    ).first()
    if membership is None:
        raise ServiceError("card not found", 404)
    return card, column.board_id


def create_comment(card_id, user_id, content):
    card, board_id = _board_id_for_card(card_id, user_id)
    content = content.strip()
    comment = Comment(card_id=card.id, author_id=user_id, content=content)
    db.session.add(comment)
    db.session.flush()

    db.session.add(
        ActivityEvent(
            board_id=board_id,
            actor_id=user_id,
            type="comment_created",
            card_id=card.id,
            comment_id=comment.id,
        )
    )

    author = db.session.get(User, user_id)
    if card.assignee_id is not None and card.assignee_id != user_id:
        actor_name = author.name if author else "Someone"
        db.session.add(
            Notification(
                user_id=card.assignee_id,
                actor_id=user_id,
                board_id=board_id,
                card_id=card.id,
                type="comment_added",
                message=f"{actor_name} commented on a card assigned to you",
                is_read=False,
            )
        )
    db.session.commit()
    return serialize(comment, author)


def list_comments(card_id, user_id):
    card, _ = _board_id_for_card(card_id, user_id)
    rows = (
        db.session.query(Comment, User)
        .outerjoin(User, User.id == Comment.author_id)
        .filter(Comment.card_id == card.id)
        .order_by(Comment.created_at.asc())
        .all()
    )
    return [serialize(c, u) for c, u in rows]


def _owned_comment(comment_id, user_id):
    comment = db.session.get(Comment, _uuid(comment_id))
    if comment is None:
        raise ServiceError("comment not found", 404)
    # Non-members (or soft-deleted card) see 404.
    _board_id_for_card(comment.card_id, user_id)
    if comment.author_id != user_id:
        raise ServiceError("only the comment owner can do this", 403)
    return comment


def update_comment(comment_id, user_id, content):
    comment = _owned_comment(comment_id, user_id)
    comment.content = content.strip()
    comment.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return serialize(comment)


def delete_comment(comment_id, user_id):
    comment = _owned_comment(comment_id, user_id)
    cid = str(comment.id)
    db.session.delete(comment)
    db.session.commit()
    return {"id": cid}
