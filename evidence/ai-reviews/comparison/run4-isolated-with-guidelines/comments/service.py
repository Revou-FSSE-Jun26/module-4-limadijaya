from sqlalchemy import select
from werkzeug.exceptions import Forbidden, NotFound

from app.clock import utc_now
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

from .schema import CommentInputSchema

NOT_FOUND_MESSAGE = "Resource not found."


def _require_member(user_id, board_id):
    """404 for a non-member, with the same body as a missing resource (BE-08, BE-09)."""
    membership = db.session.execute(
        select(BoardMembership).where(
            BoardMembership.user_id == user_id,
            BoardMembership.board_id == board_id,
        )
    ).scalar_one_or_none()
    if membership is None:
        raise NotFound(NOT_FOUND_MESSAGE)
    return membership


def _get_live_card(card_id, lock=False):
    """Return (card, board_id). 404 if the card or its column is missing or soft-deleted (BE-11)."""
    stmt = select(Card).where(Card.id == card_id)
    if lock:
        stmt = stmt.with_for_update(read=True)  # FOR SHARE for comment creation (BE-17)
    card = db.session.execute(stmt).scalar_one_or_none()
    if card is None or card.deleted_at is not None:
        raise NotFound(NOT_FOUND_MESSAGE)
    column = db.session.execute(
        select(BoardColumn).where(BoardColumn.id == card.column_id)
    ).scalar_one_or_none()
    if column is None or column.deleted_at is not None:
        raise NotFound(NOT_FOUND_MESSAGE)
    return card, column.board_id


def _get_comment_for_owner(user_id, comment_id):
    """Order: comment/card 404, membership 404, ownership 403."""
    comment = db.session.get(Comment, comment_id)
    if comment is None:
        raise NotFound(NOT_FOUND_MESSAGE)
    _, board_id = _get_live_card(comment.card_id)
    _require_member(user_id, board_id)
    if comment.author_id != user_id:
        raise Forbidden("Only the comment author can do this.")
    return comment


def _view(comment, author):
    return {
        "id": comment.id,
        "card_id": comment.card_id,
        "content": comment.content,
        "author": {"id": author.id, "name": author.name},
        "created_at": comment.created_at,
        "updated_at": comment.updated_at,
    }


def create_comment(user_id, card_id, raw):
    try:
        card, board_id = _get_live_card(card_id, lock=True)
        _require_member(user_id, board_id)
        payload = CommentInputSchema().load(raw)  # 400 only after 404/403 checks

        now = utc_now()  # one clock reading for the whole request
        author = db.session.get(User, user_id)
        comment = Comment(
            card_id=card.id,
            author_id=user_id,
            content=payload["content"],
            created_at=now,
            updated_at=now,
        )
        db.session.add(comment)
        db.session.flush()  # assigns comment.id for the event

        db.session.add(
            ActivityEvent(
                board_id=board_id,
                actor_id=user_id,
                type="comment_created",
                card_id=card.id,
                comment_id=comment.id,
                created_at=now,
            )
        )
        if card.assignee_id is not None and card.assignee_id != user_id:
            db.session.add(
                Notification(
                    user_id=card.assignee_id,
                    actor_id=user_id,
                    board_id=board_id,
                    card_id=card.id,
                    type="comment_added",
                    message=f"{author.name} commented on a card assigned to you.",
                    is_read=False,
                    created_at=now,
                )
            )
        db.session.commit()
        return _view(comment, author)
    except Exception:
        db.session.rollback()
        raise


def list_comments(user_id, card_id):
    _, board_id = _get_live_card(card_id)
    _require_member(user_id, board_id)
    rows = db.session.execute(
        select(Comment, User)
        .join(User, User.id == Comment.author_id)
        .where(Comment.card_id == card_id)
        .order_by(Comment.created_at.asc(), Comment.id.asc())
    ).all()
    return [_view(comment, author) for comment, author in rows]


def update_comment(user_id, comment_id, raw):
    try:
        comment = _get_comment_for_owner(user_id, comment_id)
        payload = CommentInputSchema().load(raw)  # 400 only after 404/403 checks
        if payload["content"] != comment.content:
            comment.content = payload["content"]
            comment.updated_at = utc_now()
        author = db.session.get(User, comment.author_id)
        db.session.commit()
        return _view(comment, author)
    except Exception:
        db.session.rollback()
        raise


def delete_comment(user_id, comment_id):
    try:
        comment = _get_comment_for_owner(user_id, comment_id)
        deleted_id = comment.id
        db.session.delete(comment)  # hard delete; no activity event (BE-14)
        db.session.commit()
        return {"id": deleted_id}
    except Exception:
        db.session.rollback()
        raise
