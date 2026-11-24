from flask import request

from app.auth import protected
from app.blueprints.users import bp
from app.blueprints.users.schema import ProfileSchema
from app.blueprints.users.service import get_profile, update_profile
from app.responses import ok


def dump(user):
    return {"id": str(user.id), "name": user.name, "email": user.email, "created_at": user.created_at.isoformat() if user.created_at else None}


@bp.get("/users/me")
@protected
def profile():
    return ok(dump(get_profile()))


@bp.patch("/users/me")
@protected
def patch_profile():
    return ok(dump(update_profile(ProfileSchema().load(request.get_json() or {}))))
