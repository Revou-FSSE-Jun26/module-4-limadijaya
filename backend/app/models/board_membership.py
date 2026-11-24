"""Board membership model."""

from app.extensions import db
from app.models import timestamp_column, uuid_primary_key


class BoardMembership(db.Model):
    __tablename__ = "board_memberships"
    __table_args__ = (
        db.UniqueConstraint(
            "board_id",
            "user_id",
            name="uq_board_memberships_board_user",
        ),
        db.CheckConstraint(
            "role IN ('administrator', 'member')",
            name="ck_board_memberships_role",
        ),
    )

    id = uuid_primary_key()
    board_id = db.Column(
        db.ForeignKey("boards.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = db.Column(db.ForeignKey("users.id"), nullable=False)
    role = db.Column(db.Text, nullable=False)
    created_at = timestamp_column()
