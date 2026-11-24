from ..extensions import db
from ._base import timestamp, uuid_fk, uuid_pk


class BoardColumn(db.Model):
    """Table `columns`. Named BoardColumn to avoid a clash with sqlalchemy.Column."""

    __tablename__ = "columns"
    __table_args__ = (
        db.Index(
            "ix_columns_board_live", "board_id", "position", postgresql_where=db.text("deleted_at IS NULL")
        ),
    )

    id = uuid_pk()
    board_id = uuid_fk("boards.id", ondelete="CASCADE")
    name = db.Column(db.Text, nullable=False)
    position = db.Column(db.Float, nullable=False)  # exposed as `order` (DB-05)
    is_done = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())
    deleted_at = timestamp(nullable=True)
    created_at = timestamp()
    updated_at = timestamp()