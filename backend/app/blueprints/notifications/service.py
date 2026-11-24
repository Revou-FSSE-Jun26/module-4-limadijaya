from sqlalchemy import func, select

from ...errors import BadRequestError, NotFoundError
from ...extensions import db
from ...models import Notification, User
from ...schemas_common import load_query
from .schema import MAX_PER_PAGE, NotificationQuerySchema, NotificationSchema


def _dump(notification: Notification, actor: User) -> dict:
    return NotificationSchema().dump(
        {
            "id": notification.id,
            "type": notification.type,
            "message": notification.message,
            "board_id": notification.board_id,
            "card_id": notification.card_id,
            "actor": {"id": actor.id, "name": actor.name},
            "is_read": notification.is_read,
            "created_at": notification.created_at,
        }
    )


def list_notifications(user_id, args) -> dict:
    query = load_query(NotificationQuerySchema(), args)
    page, per_page = query["page"], query["per_page"]
    if per_page > MAX_PER_PAGE:
        raise BadRequestError(f"Invalid request: per_page: must be at most {MAX_PER_PAGE}.")
    mine = Notification.user_id == user_id
    total = db.session.execute(select(func.count()).select_from(Notification).where(mine)).scalar_one()
    unread = db.session.execute(
        select(func.count()).select_from(Notification).where(mine, Notification.is_read.is_(False))
    ).scalar_one()
    rows = db.session.execute(
        select(Notification, User)
        .join(User, User.id == Notification.actor_id)
        .where(mine)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .limit(per_page)
        .offset((page - 1) * per_page)
    ).all()
    return {
        "items": [_dump(n, actor) for n, actor in rows],
        "page": page,
        "per_page": per_page,
        "total": total,
        "unread_count": unread,
    }


def mark_read(user_id, notification_id) -> dict:
    notification = db.session.get(Notification, notification_id)
    if notification is None or notification.user_id != user_id:
        raise NotFoundError()  # identical for missing and for another user's notification
    if not notification.is_read:
        notification.is_read = True
        db.session.commit()
    return _dump(notification, db.session.get(User, notification.actor_id))