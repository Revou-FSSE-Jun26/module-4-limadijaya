"""Row locks. Lock order is board, then columns, then cards (BE-17, DB-14).

Every helper re-reads the row after taking the lock (populate_existing), so the caller
sees current data and not a stale identity-map copy.
"""
from sqlalchemy import select

from .extensions import db
from .models import Board, BoardColumn, Card


def _lock(model, row_id, share=False):
    stmt = select(model).where(model.id == row_id).with_for_update(read=share)
    return db.session.execute(stmt.execution_options(populate_existing=True)).scalar_one_or_none()


def lock_board(board_id):
    return _lock(Board, board_id)


def lock_column(column_id):
    return _lock(BoardColumn, column_id)


def lock_card(card_id, share=False):
    return _lock(Card, card_id, share=share)