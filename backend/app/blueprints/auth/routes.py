from flask import Blueprint

from ...http import read_json_body
from ...responses import ok
from ..users.schema import UserSchema
from . import service

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/auth/register")
def register():
    user = service.register(read_json_body())
    return ok(UserSchema().dump(user), 201)


@auth_bp.post("/auth/login")
def login():
    token = service.login(read_json_body())
    return ok({"access_token": token})