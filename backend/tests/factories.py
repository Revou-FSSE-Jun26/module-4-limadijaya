"""Data factories. Tests create their own data and never touch production (TEST-001-AC03)."""
from __future__ import annotations

import itertools
from datetime import datetime, timezone

from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models import Board, BoardColumn, BoardMembership, Card, User
from app.security import hash_password

PASSWORD = "password123"
_counter = itertools.count(1)
_hash_cache: dict[str, str] = {}
EPOCH = datetime(2026, 11, 20, 9, 0, 0, tzinfo=timezone.utc)


def _hash() -> str:
    # One scrypt hash is reused, so a test run does not spend time hashing for every user.
    if PASSWORD not in _hash_cache:
        _hash_cache[PASSWORD] = hash_password(PASSWORD)
    return _hash_cache[PASSWORD]


def make_user(name: str | None = None, email: str | None = None) -> User:
    n = next(_counter)
    user = User(
        name=name or f"User {n}",
        email=email or f"user{n}@example.com",
        password_hash=_hash(),
        created_at=EPOCH,
        updated_at=EPOCH,
    )
    db.session.add(user)
    db.session.commit()
    return user


def auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(identity=str(user.id))}"}


def make_board(owner: User, name: str = "Sprint board") -> Board:
    board = Board(name=name, created_at=EPOCH, updated_at=EPOCH)
    db.session.add(board)
    db.session.flush()
    db.session.add(BoardMembership(board_id=board.id, user_id=owner.id, role="administrator", created_at=EPOCH))
    db.session.commit()
    return board


def add_member(board: Board, user: User, role: str = "member") -> None:
    db.session.add(BoardMembership(board_id=board.id, user_id=user.id, role=role, created_at=EPOCH))
    db.session.commit()


def make_column(board: Board, name: str = "To do", position: float = 1024.0, is_done: bool = False) -> BoardColumn:
    column = BoardColumn(
        board_id=board.id, name=name, position=position, is_done=is_done, created_at=EPOCH, updated_at=EPOCH
    )
    db.session.add(column)
    db.session.commit()
    return column


def make_card(column: BoardColumn, title: str = "Write spec", position: float = 1024.0, assignee: User | None = None) -> Card:
    card = Card(
        column_id=column.id,
        title=title,
        position=position,
        assignee_id=assignee.id if assignee else None,
        created_at=EPOCH,
        updated_at=EPOCH,
    )
    db.session.add(card)
    db.session.commit()
    return card