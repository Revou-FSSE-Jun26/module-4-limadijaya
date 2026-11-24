from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from ...access import require_admin, require_member
from ...clock import utcnow
from ...errors import ConflictError, NotFoundError
from ...extensions import db
from ...locking import lock_board
from ...models import Board, BoardColumn, BoardMembership, Card, User
from ...models.board_membership import ROLE_ADMIN, ROLE_MEMBER
from ...schemas_common import require_object
from ..cards.schema import CardSchema
from ..columns.schema import ColumnSchema
from ..users.schema import MemberRefSchema
from .schema import AddMemberSchema, BoardNameSchema


def create_board(user_id, raw) -> Board:
    data = BoardNameSchema().load(require_object(raw))
    now = utcnow()
    board = Board(name=data["name"], created_at=now, updated_at=now)
    db.session.add(board)
    db.session.flush()
    db.session.add(BoardMembership(board_id=board.id, user_id=user_id, role=ROLE_ADMIN, created_at=now))
    db.session.commit()
    return board


def list_boards(user_id) -> list[Board]:
    stmt = (
        select(Board)
        .join(BoardMembership, BoardMembership.board_id == Board.id)
        .where(BoardMembership.user_id == user_id)
        .order_by(Board.created_at, Board.id)
    )
    return list(db.session.execute(stmt).scalars())


def get_board_detail(user_id, board_id) -> dict:
    """Board, members, live columns, and live cards in a fixed number of queries (BOARD-003)."""
    membership = require_member(user_id, board_id)
    board = db.session.get(Board, board_id)
    if board is None:
        raise NotFoundError()

    members = db.session.execute(
        select(User.id, User.name)
        .join(BoardMembership, BoardMembership.user_id == User.id)
        .where(BoardMembership.board_id == board_id)
        .order_by(User.name, User.id)
    ).all()
    columns = list(
        db.session.execute(
            select(BoardColumn)
            .where(BoardColumn.board_id == board_id, BoardColumn.deleted_at.is_(None))
            .order_by(BoardColumn.position, BoardColumn.created_at, BoardColumn.id)
        ).scalars()
    )
    cards_by_column: dict = {column.id: [] for column in columns}
    if columns:
        cards = db.session.execute(
            select(Card)
            .where(Card.column_id.in_(list(cards_by_column)), Card.deleted_at.is_(None))
            .order_by(Card.position, Card.created_at, Card.id)
        ).scalars()
        for card in cards:
            cards_by_column[card.column_id].append(card)

    column_schema, card_schema = ColumnSchema(), CardSchema()
    return {
        "id": str(board.id),
        "name": board.name,
        "role": membership.role,
        "members": MemberRefSchema(many=True).dump([{"id": m.id, "name": m.name} for m in members]),
        "columns": [
            {**column_schema.dump(column), "cards": card_schema.dump(cards_by_column[column.id], many=True)}
            for column in columns
        ],
    }


def update_board(user_id, board_id, raw) -> Board:
    membership = require_member(user_id, board_id)
    require_admin(membership)
    data = BoardNameSchema().load(require_object(raw))
    board = db.session.get(Board, board_id)
    if board is None:
        raise NotFoundError()
    if board.name != data["name"]:
        board.name = data["name"]
        board.updated_at = utcnow()
        db.session.commit()
    return board


def delete_board(user_id, board_id) -> dict:
    membership = require_member(user_id, board_id)
    require_admin(membership)
    if lock_board(board_id) is None:
        raise NotFoundError()
    # A Core DELETE lets PostgreSQL ON DELETE CASCADE remove every dependent row (DA-14).
    db.session.execute(delete(Board).where(Board.id == board_id))
    db.session.commit()
    return {"id": str(board_id)}


def add_member(user_id, board_id, raw) -> User:
    membership = require_member(user_id, board_id)
    require_admin(membership)
    data = AddMemberSchema().load(require_object(raw))
    target = db.session.execute(select(User).where(User.email == data["email"])).scalar_one_or_none()
    if target is None:
        raise NotFoundError()
    if db.session.execute(
        select(BoardMembership.id).where(
            BoardMembership.board_id == board_id, BoardMembership.user_id == target.id
        )
    ).first():
        raise ConflictError("This user is already a member of the board.")
    db.session.add(
        BoardMembership(board_id=board_id, user_id=target.id, role=ROLE_MEMBER, created_at=utcnow())
    )
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ConflictError("This user is already a member of the board.") from None
    return target