from app.auth import current_user_id, require_membership
from app.clock import utc_now
from app.errors import ForbiddenError, NotFoundError
from app.extensions import db
from app.models import BoardColumn, Card, Comment


def card(card_id):
    value = db.session.get(Card, card_id)
    if value is None or value.deleted_at is not None: raise NotFoundError()
    column = db.session.get(BoardColumn, value.column_id); require_membership(column.board_id); return value


def create(card_id, data):
    card(card_id); now = utc_now(); value = Comment(card_id=card_id, author_id=current_user_id(), content=data["content"].strip(), created_at=now, updated_at=now); db.session.add(value); db.session.commit(); return value


def list_for_card(card_id): card(card_id); return Comment.query.filter_by(card_id=card_id).order_by(Comment.created_at).all()


def update(comment_id, data):
    value = db.session.get(Comment, comment_id)
    if value is None: raise NotFoundError()
    if value.author_id != current_user_id(): raise ForbiddenError()
    value.content = data["content"].strip(); value.updated_at = utc_now(); db.session.commit(); return value


def remove(comment_id):
    value = db.session.get(Comment, comment_id)
    if value is None: raise NotFoundError()
    if value.author_id != current_user_id(): raise ForbiddenError()
    db.session.delete(value); db.session.commit()
