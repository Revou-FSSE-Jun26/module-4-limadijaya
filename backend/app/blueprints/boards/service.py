from app.auth import current_user_id, require_membership
from app.clock import utc_now
from app.errors import NotFoundError
from app.extensions import db
from app.models import Board, BoardColumn, BoardMembership, Card, User


def dump(board, nested=False):
    value = {"id": str(board.id), "name": board.name, "created_at": board.created_at.isoformat() if board.created_at else None}
    if nested:
        columns = BoardColumn.query.filter_by(board_id=board.id, deleted_at=None).order_by(BoardColumn.position).all()
        value["columns"] = [{"id": str(c.id), "name": c.name, "order": c.position, "is_done": c.is_done, "cards": [{"id": str(x.id), "title": x.title, "order": x.position, "assignee_id": str(x.assignee_id) if x.assignee_id else None} for x in Card.query.filter_by(column_id=c.id, deleted_at=None).order_by(Card.position).all()]} for c in columns]
    return value


def create(data):
    now = utc_now(); board = Board(name=data["name"].strip(), created_at=now, updated_at=now)
    db.session.add(board)
    db.session.flush()
    db.session.add(BoardMembership(board_id=board.id, user_id=current_user_id(), role="administrator", created_at=now))
    db.session.commit()
    return board


def list_for_user():
    return Board.query.join(BoardMembership).filter(BoardMembership.user_id == current_user_id()).order_by(Board.created_at).all()


def get(board_id):
    board = db.session.get(Board, board_id)
    if board is None:
        raise NotFoundError()
    require_membership(board_id)
    return board


def update(board_id, data):
    board = get(board_id)
    membership = require_membership(board_id)
    if membership.role != "administrator":
        from app.errors import ForbiddenError
        raise ForbiddenError()
    board.name = data["name"].strip(); board.updated_at = utc_now()
    db.session.commit()
    return board


def delete(board_id):
    board = get(board_id)
    membership = require_membership(board_id)
    if membership.role != "administrator":
        from app.errors import ForbiddenError
        raise ForbiddenError()
    db.session.delete(board)
    db.session.commit()
    return board_id


def add_member(board_id, data):
    membership = require_membership(board_id)
    if membership.role != "administrator":
        from app.errors import ForbiddenError
        raise ForbiddenError()
    user = User.query.filter_by(email=data["email"].strip().lower()).first()
    if user is None:
        raise NotFoundError()
    existing = BoardMembership.query.filter_by(board_id=board_id, user_id=user.id).first()
    if existing:
        from app.errors import ConflictError
        raise ConflictError("User is already a board member.")
    value = BoardMembership(board_id=board_id, user_id=user.id, role="member", created_at=utc_now())
    db.session.add(value); db.session.commit(); return value
