from flask import Blueprint
from flask_jwt_extended import jwt_required

from ...http import current_user_id, read_json_body
from ...responses import ok
from . import service
from .schema import UserSchema

users_bp = Blueprint("users", __name__)


@users_bp.get("/users/me")
@jwt_required()
def get_me():
    return ok(UserSchema().dump(service.get_me(current_user_id())))


@users_bp.patch("/users/me")
@jwt_required()
def update_me():
    user = service.update_me(current_user_id(), read_json_body())
    return ok(UserSchema().dump(user))