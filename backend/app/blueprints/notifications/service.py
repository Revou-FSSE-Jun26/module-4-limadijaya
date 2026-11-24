from app.auth import current_user_id
from app.errors import NotFoundError
from app.extensions import db
from app.models import Notification


def list_for_user(page=1, per_page=20):
    query = Notification.query.filter_by(user_id=current_user_id()).order_by(Notification.created_at.desc())
    return query.offset((page - 1) * per_page).limit(per_page).all()


def mark_read(notification_id):
    value = db.session.get(Notification, notification_id)
    if value is None or value.user_id != current_user_id(): raise NotFoundError()
    value.is_read = True; db.session.commit(); return value
