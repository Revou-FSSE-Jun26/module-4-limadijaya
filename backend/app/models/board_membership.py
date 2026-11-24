from ..extensions import db
from ._base import timestamp, uuid_fk, uuid_pk

ROLE_ADMIN = "administrator"
ROLE_MEMBER = "member"


class BoardMembership(db.Model):
    __tablename__ = "board_memberships"
    __table_args__ = (
        db.UniqueConstraint("board_id", "user_id", name="uq_membership_board_user"),
        db.CheckConstraint("role IN ('administrator','member')", name="ck_membership_role"),
    )

    id = uuid_pk()
    board_id = uuid_fk("boards.id", ondelete="CASCADE")
    user_id = uuid_fk("users.id", index=True)
    role = db.Column(db.Text, nullable=False)
    created_at = timestamp()