"""Weekly board analytics. Every metric is one SQLAlchemy statement with joins (BE-15)."""
from datetime import timedelta

from sqlalchemy import and_, func, select

from ...access import require_member
from ...clock import utcnow
from ...extensions import db
from ...models import ActivityEvent, BoardColumn, BoardMembership, Card, User
from ...schemas_common import iso, load_query
from .schema import AnalyticsQuerySchema


def week_window(now):
    """Monday 00:00:00 UTC up to the next Monday, end exclusive."""
    start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    return start, start + timedelta(days=7)


def get_analytics(user_id, board_id, args) -> dict:
    require_member(user_id, board_id)
    load_query(AnalyticsQuerySchema(), args)
    start, end = week_window(utcnow())  # one clock reading for the whole response

    per_column = db.session.execute(
        select(BoardColumn.id, BoardColumn.name, func.count(Card.id))
        .select_from(BoardColumn)
        .outerjoin(Card, and_(Card.column_id == BoardColumn.id, Card.deleted_at.is_(None)))
        .where(BoardColumn.board_id == board_id, BoardColumn.deleted_at.is_(None))
        .group_by(BoardColumn.id)
        .order_by(BoardColumn.position, BoardColumn.id)
    ).all()

    completed = db.session.execute(
        select(func.count(Card.id))
        .select_from(Card)
        .join(BoardColumn, BoardColumn.id == Card.column_id)
        .where(
            BoardColumn.board_id == board_id,
            BoardColumn.deleted_at.is_(None),
            BoardColumn.is_done.is_(True),
            Card.deleted_at.is_(None),
            Card.completed_at >= start,
            Card.completed_at < end,
        )
    ).scalar_one()

    activity = db.session.execute(
        select(User.id, User.name, func.count(ActivityEvent.id).label("activity_count"))
        .select_from(BoardMembership)
        .join(User, User.id == BoardMembership.user_id)
        .outerjoin(
            ActivityEvent,
            and_(
                ActivityEvent.actor_id == User.id,
                ActivityEvent.board_id == board_id,
                ActivityEvent.created_at >= start,
                ActivityEvent.created_at < end,
            ),
        )
        .where(BoardMembership.board_id == board_id)
        .group_by(User.id)
        .order_by(func.count(ActivityEvent.id).desc(), User.name, User.id)
    ).all()

    return {
        "window": {"start": iso(start).replace(".000000", ""), "end": iso(end).replace(".000000", "")},
        "cards_per_column": [
            {"column_id": str(cid), "name": name, "card_count": count} for cid, name, count in per_column
        ],
        "completed_this_week": completed,
        "member_activity": [
            {"user_id": str(uid), "name": name, "activity_count": count} for uid, name, count in activity
        ],
    }