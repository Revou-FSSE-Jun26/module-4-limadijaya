from datetime import datetime, timedelta, timezone

from sqlalchemy import func

from app.auth import require_membership
from app.extensions import db
from app.models import ActivityEvent, BoardColumn, Card


def get(board_id):
    require_membership(board_id)
    columns = BoardColumn.query.filter_by(board_id=board_id, deleted_at=None).order_by(BoardColumn.position).all()
    week_start = datetime.now(timezone.utc) - timedelta(days=7)
    completed = db.session.query(func.count(Card.id)).join(BoardColumn, Card.column_id == BoardColumn.id).filter(BoardColumn.board_id == board_id, Card.completed_at >= week_start, Card.deleted_at.is_(None)).scalar() or 0
    activity = db.session.query(ActivityEvent.actor_id, func.count(ActivityEvent.id)).filter(ActivityEvent.board_id == board_id).group_by(ActivityEvent.actor_id).all()
    return {"cards_per_column": [{"column_id": str(column.id), "name": column.name, "count": Card.query.filter_by(column_id=column.id, deleted_at=None).count()} for column in columns], "cards_completed_this_week": completed, "member_activity": [{"user_id": str(user_id), "count": count} for user_id, count in activity]}
