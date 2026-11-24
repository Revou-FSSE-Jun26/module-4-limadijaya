from datetime import datetime, timezone

from app.auth import current_user_id, require_membership
from app.clock import utc_now
from app.errors import NotFoundError
from app.extensions import db
from app.models import BoardColumn, Card, Notification


def get(card_id):
    card = db.session.get(Card, card_id)
    if card is None or card.deleted_at is not None:
        raise NotFoundError()
    require_membership(db.session.get(BoardColumn, card.column_id).board_id)
    return card


def create(column_id, data):
    column = db.session.get(BoardColumn, column_id)
    if column is None or column.deleted_at is not None: raise NotFoundError()
    require_membership(column.board_id)
    last = Card.query.filter_by(column_id=column_id, deleted_at=None).order_by(Card.position.desc()).first()
    now = utc_now(); card = Card(column_id=column_id, title=data["title"].strip(), assignee_id=data.get("assignee_id"), position=(last.position + 1024 if last else 1024), created_at=now, updated_at=now)
    db.session.add(card); db.session.flush()
    if card.assignee_id and card.assignee_id != current_user_id():
        db.session.add(Notification(user_id=card.assignee_id, actor_id=current_user_id(), board_id=column.board_id, card_id=card.id, type="card_assigned", message=f"{card.title} was assigned to you", created_at=now))
    db.session.commit(); return card


def update(card_id, data):
    card = get(card_id); previous_assignee = card.assignee_id; card.title = data["title"].strip(); card.assignee_id = data.get("assignee_id"); card.updated_at = utc_now()
    if card.assignee_id and card.assignee_id != previous_assignee and card.assignee_id != current_user_id():
        board_id = db.session.get(BoardColumn, card.column_id).board_id
        db.session.add(Notification(user_id=card.assignee_id, actor_id=current_user_id(), board_id=board_id, card_id=card.id, type="card_assigned", message=f"{card.title} was assigned to you", created_at=card.updated_at))
    db.session.commit(); return card


def remove(card_id):
    card = get(card_id); card.deleted_at = datetime.now(timezone.utc); db.session.commit()


def move(card_id, data):
    card = get(card_id)
    column = db.session.get(BoardColumn, data["column_id"])
    if column is None or column.deleted_at is not None: raise NotFoundError()
    require_membership(column.board_id); card.column_id = column.id; card.position = data["order"]; card.updated_at = utc_now(); db.session.commit(); return card


def assigned():
    return Card.query.filter_by(assignee_id=current_user_id(), deleted_at=None).all()
