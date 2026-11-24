from sqlalchemy import func, select

from ...access import get_live_column_or_404, require_admin, require_member
from ...clock import utcnow
from ...errors import BadRequestError, ConflictError, NotFoundError
from ...extensions import db
from ...locking import lock_board, lock_column
from ...models import BoardColumn, Card
from ...queries import live_columns
from ...schemas_common import require_object
from .schema import CreateColumnSchema, ReorderSchema, UpdateColumnSchema

SPACING = 1024.0  # A-01: a new column gets max(live position) + SPACING
INVALID_COLUMNS = "One or more columns are invalid."


def create_column(user_id, board_id, raw) -> BoardColumn:
    require_member(user_id, board_id)
    data = CreateColumnSchema().load(require_object(raw))
    if lock_board(board_id) is None:  # serializes with reorder and delete (UD-20)
        raise NotFoundError()
    top = db.session.execute(
        select(func.max(BoardColumn.position)).where(
            BoardColumn.board_id == board_id, BoardColumn.deleted_at.is_(None)
        )
    ).scalar()
    now = utcnow()
    column = BoardColumn(
        board_id=board_id,
        name=data["name"],
        position=SPACING if top is None else top + SPACING,
        is_done=False,
        created_at=now,
        updated_at=now,
    )
    db.session.add(column)
    db.session.commit()
    return column


def reorder_columns(user_id, board_id, raw) -> list[BoardColumn]:
    require_member(user_id, board_id)
    data = ReorderSchema().load(require_object(raw))
    submitted = {entry["id"]: entry["order"] for entry in data["columns"]}
    now = utcnow()
    if lock_board(board_id) is None:
        raise NotFoundError()
    active = list(db.session.execute(live_columns(board_id).execution_options(populate_existing=True)).scalars())
    by_id = {column.id: column for column in active}
    if any(column_id not in by_id for column_id in submitted):
        raise BadRequestError(INVALID_COLUMNS)
    final = {column.id: column.position for column in active}
    final.update(submitted)
    if len(set(final.values())) != len(final):
        raise ConflictError("An order value collides with another column.")
    for column_id in sorted(submitted, key=str):
        column = by_id[column_id]
        if column.position != submitted[column_id]:
            column.position = submitted[column_id]
            column.updated_at = now
    db.session.commit()
    return sorted(active, key=lambda c: (c.position, c.created_at, str(c.id)))


def update_column(user_id, column_id, raw) -> BoardColumn:
    column = get_live_column_or_404(column_id)
    membership = require_member(user_id, column.board_id)
    # The is_done key is administrator-only whatever its value, and is tested before validation.
    if isinstance(raw, dict) and "is_done" in raw:
        require_admin(membership)
    data = UpdateColumnSchema().load(require_object(raw))
    if not data:
        raise BadRequestError("Invalid request: provide name or is_done.")
    now = utcnow()
    if "is_done" in data:
        column = lock_column(column_id)
        if column is None or column.deleted_at is not None:
            raise NotFoundError()
    if "name" in data and column.name != data["name"]:
        column.name = data["name"]
        column.updated_at = now
    if "is_done" in data and column.is_done != data["is_done"]:
        column.is_done = data["is_done"]
        column.updated_at = now
        cards = db.session.execute(
            select(Card).where(Card.column_id == column.id, Card.deleted_at.is_(None)).order_by(Card.id)
        ).scalars()
        for card in cards:
            card.completed_at = now if column.is_done else None
            card.updated_at = now
    db.session.commit()
    return column


def delete_column(user_id, column_id) -> dict:
    column = get_live_column_or_404(column_id)
    require_admin(require_member(user_id, column.board_id))
    now = utcnow()
    if lock_board(column.board_id) is None:
        raise NotFoundError()
    column = lock_column(column_id)
    if column is None or column.deleted_at is not None:
        raise NotFoundError()
    cards = db.session.execute(
        select(Card).where(Card.column_id == column.id, Card.deleted_at.is_(None)).order_by(Card.id)
    ).scalars()
    for card in cards:  # same deleted_at for the column and its live cards (COLUMN-003-AC04)
        card.deleted_at = now
    column.deleted_at = now
    db.session.commit()
    return {"id": str(column_id)}