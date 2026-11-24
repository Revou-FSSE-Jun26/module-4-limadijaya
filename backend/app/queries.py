"""The only way services read columns and cards (BE-11, DB-12). Soft-deleted rows stay invisible."""
from sqlalchemy import select

from .models import BoardColumn, Card


def live_columns(board_id):
    return select(BoardColumn).where(BoardColumn.board_id == board_id, BoardColumn.deleted_at.is_(None))


def live_cards(column_id):
    return select(Card).where(Card.column_id == column_id, Card.deleted_at.is_(None))