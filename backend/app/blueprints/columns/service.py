from datetime import datetime, timezone

from app.auth import require_membership
from app.clock import utc_now
from app.errors import NotFoundError
from app.extensions import db
from app.models import BoardColumn


def create(board_id, data):
    require_membership(board_id)
    last = BoardColumn.query.filter_by(board_id=board_id, deleted_at=None).order_by(BoardColumn.position.desc()).first()
    now = utc_now(); column = BoardColumn(board_id=board_id, name=data["name"].strip(), is_done=data.get("is_done", False), position=(last.position + 1024 if last else 1024), created_at=now, updated_at=now)
    db.session.add(column); db.session.commit(); return column


def get(column_id):
    column = db.session.get(BoardColumn, column_id)
    if column is None or column.deleted_at is not None:
        raise NotFoundError()
    require_membership(column.board_id)
    return column


def update(column_id, data):
    column = get(column_id); column.name = data["name"].strip(); column.updated_at = utc_now(); db.session.commit(); return column


def remove(column_id):
    column = get(column_id); column.deleted_at = datetime.now(timezone.utc); db.session.commit()


def reorder(board_id, data):
    require_membership(board_id)
    columns = BoardColumn.query.filter_by(board_id=board_id, deleted_at=None).all()
    by_id = {column.id: column for column in columns}
    for index, column_id in enumerate(data["ids"], 1):
        if column_id not in by_id: raise NotFoundError()
        by_id[column_id].position = index * 1024.0
    db.session.commit(); return sorted(columns, key=lambda column: column.position)
