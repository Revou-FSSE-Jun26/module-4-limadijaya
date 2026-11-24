"""Membership, role, and ownership checks (BE-08, BE-09, BE-10).

All lookups raise the same NotFoundError, so a response never reveals whether a resource
exists to someone who may not see it. Authorization data is read from the database on every
request and never from token claims.
"""
from __future__ import annotations

from sqlalchemy import select

from .errors import ForbiddenError, NotFoundError
from .extensions import db
from .models import BoardColumn, BoardMembership, Card, Comment
from .models.board_membership import ROLE_ADMIN


def get_membership(user_id, board_id):
    return db.session.execute(
        select(BoardMembership).where(BoardMembership.user_id == user_id, BoardMembership.board_id == board_id)
    ).scalar_one_or_none()


def require_member(user_id, board_id) -> BoardMembership:
    membership = get_membership(user_id, board_id)
    if membership is None:
        raise NotFoundError()
    return membership


def require_admin(membership: BoardMembership) -> None:
    if membership.role != ROLE_ADMIN:
        raise ForbiddenError()


def require_comment_owner(user_id, comment: Comment) -> None:
    if comment.author_id != user_id:
        raise ForbiddenError()


def get_live_column_or_404(column_id) -> BoardColumn:
    column = db.session.get(BoardColumn, column_id)
    if column is None or column.deleted_at is not None:
        raise NotFoundError()
    return column


def get_live_card_or_404(card_id) -> tuple[Card, BoardColumn]:
    card = db.session.get(Card, card_id)
    if card is None or card.deleted_at is not None:
        raise NotFoundError()
    column = db.session.get(BoardColumn, card.column_id)
    if column is None or column.deleted_at is not None:
        raise NotFoundError()
    return card, column


def get_comment_or_404(comment_id) -> tuple[Comment, Card, BoardColumn]:
    comment = db.session.get(Comment, comment_id)
    if comment is None:
        raise NotFoundError()
    card, column = get_live_card_or_404(comment.card_id)
    return comment, card, column