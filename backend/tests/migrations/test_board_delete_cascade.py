"""Board hard-delete cascade proof (T2.11, DA-14, V-04).

Builds a fully populated board, deletes only the board row, and lets PostgreSQL ON DELETE CASCADE
remove every dependent row, including soft-deleted ones. Users and other boards must be untouched.
"""
from sqlalchemy import delete, func, select

from app.extensions import db
from app.models import ActivityEvent, Board, BoardColumn, BoardMembership, Card, Comment, Notification, User
from tests.factories import EPOCH, add_member, make_board, make_card, make_column, make_user

TABLES = (ActivityEvent, Notification, Comment, Card, BoardColumn, BoardMembership)


def count(model, **filters):
    stmt = select(func.count()).select_from(model)
    for key, value in filters.items():
        stmt = stmt.where(getattr(model, key) == value)
    return db.session.execute(stmt).scalar_one()


def test_deleting_a_board_leaves_no_dependent_row(app_context):
    owner, member = make_user(), make_user()
    board = make_board(owner)
    add_member(board, member)
    live, retired = make_column(board, "Live", 1024.0), make_column(board, "Retired", 2048.0)
    retired.deleted_at = EPOCH
    card = make_card(live, assignee=member)
    soft_deleted_card = make_card(retired, "Old", 1024.0)
    soft_deleted_card.deleted_at = EPOCH
    comment = Comment(card_id=card.id, author_id=owner.id, content="hi", created_at=EPOCH, updated_at=EPOCH)
    db.session.add(comment)
    db.session.flush()
    db.session.add(
        Notification(
            user_id=member.id, actor_id=owner.id, board_id=board.id, card_id=card.id,
            type="comment_added", message="m", created_at=EPOCH,
        )
    )
    db.session.add_all(
        [
            ActivityEvent(
                board_id=board.id, actor_id=owner.id, type="card_moved", card_id=soft_deleted_card.id,
                from_column_id=live.id, to_column_id=retired.id, created_at=EPOCH,
            ),
            ActivityEvent(
                board_id=board.id, actor_id=owner.id, type="comment_created", card_id=card.id,
                comment_id=comment.id, created_at=EPOCH,
            ),
        ]
    )
    db.session.commit()

    other_owner = make_user()
    other = make_board(other_owner, "Untouched")
    other_card = make_card(make_column(other), "Keep me")

    board_id, card_id, old_card_id = board.id, card.id, soft_deleted_card.id
    other_id, other_card_id = other.id, other_card.id
    db.session.execute(delete(Board).where(Board.id == board_id))
    db.session.commit()

    assert count(Board, id=board_id) == 0
    assert count(BoardMembership, board_id=board_id) == 0
    assert count(BoardColumn, board_id=board_id) == 0
    assert count(ActivityEvent, board_id=board_id) == 0
    assert count(Notification, board_id=board_id) == 0
    assert count(Card, id=card_id) == 0 and count(Card, id=old_card_id) == 0
    assert count(Comment, card_id=card_id) == 0
    # Nothing outside the board changed.
    assert count(User) == 3
    assert count(Board, id=other_id) == 1 and count(Card, id=other_card_id) == 1
