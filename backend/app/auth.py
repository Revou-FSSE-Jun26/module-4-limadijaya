from functools import wraps
from uuid import UUID

from flask_jwt_extended import get_jwt_identity, jwt_required

from app.errors import NotFoundError
from app.models import BoardMembership


def current_user_id():
    return UUID(str(get_jwt_identity()))


def protected(fn):
    return jwt_required()(fn)


def require_membership(board_id, user_id=None):
    from app.extensions import db

    user_id = user_id or current_user_id()
    membership = db.session.query(BoardMembership).filter_by(board_id=board_id, user_id=user_id).first()
    if membership is None:
        raise NotFoundError()
    return membership
