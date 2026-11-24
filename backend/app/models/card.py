from ..extensions import db
from ._base import timestamp, uuid_fk, uuid_pk


class Card(db.Model):
    __tablename__ = "cards"
    __table_args__ = (
        db.Index("ix_cards_column_live", "column_id", "position", postgresql_where=db.text("deleted_at IS NULL")),
        db.Index("ix_cards_assignee_live", "assignee_id", postgresql_where=db.text("deleted_at IS NULL")),
        db.Index(
            "ix_cards_completed_live",
            "column_id",
            "completed_at",
            postgresql_where=db.text("deleted_at IS NULL AND completed_at IS NOT NULL"),
        ),
    )

    id = uuid_pk()
    column_id = uuid_fk("columns.id", ondelete="CASCADE")
    title = db.Column(db.Text, nullable=False)
    position = db.Column(db.Float, nullable=False)  # exposed as `order` (DB-05)
    assignee_id = uuid_fk("users.id", nullable=True)
    completed_at = timestamp(nullable=True)
    deleted_at = timestamp(nullable=True)
    created_at = timestamp()
    updated_at = timestamp()