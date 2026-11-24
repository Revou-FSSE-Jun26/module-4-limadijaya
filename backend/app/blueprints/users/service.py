from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ...clock import utcnow
from ...errors import BadRequestError, ConflictError, NotFoundError
from ...extensions import db
from ...models import User
from ...schemas_common import require_object
from .schema import UpdateProfileSchema


def get_me(user_id) -> User:
    user = db.session.get(User, user_id)
    if user is None:
        raise NotFoundError()
    return user


def update_me(user_id, raw) -> User:
    user = get_me(user_id)
    data = UpdateProfileSchema().load(require_object(raw))
    if not data:
        raise BadRequestError("Invalid request: provide name or email.")
    changed = {k: v for k, v in data.items() if getattr(user, k) != v}
    if not changed:
        return user
    if "email" in changed:
        taken = db.session.execute(
            select(User.id).where(User.email == changed["email"], User.id != user.id)
        ).first()
        if taken:
            raise ConflictError("An account with this email already exists.")
    for key, value in changed.items():
        setattr(user, key, value)
    user.updated_at = utcnow()
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ConflictError("An account with this email already exists.") from None
    return user