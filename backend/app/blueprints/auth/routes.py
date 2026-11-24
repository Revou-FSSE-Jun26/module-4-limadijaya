from flask import request

from app.blueprints.auth import bp
from app.blueprints.auth.schema import CredentialsSchema
from app.blueprints.auth.service import login, register
from app.responses import ok


@bp.post("/auth/register")
def register_route():
    user = register(CredentialsSchema().load(request.get_json(silent=False) or {}))
    return ok({"id": str(user.id), "name": user.name, "email": user.email}, 201)


@bp.post("/auth/login")
def login_route():
    user, token = login(CredentialsSchema(only=("email", "password")).load(request.get_json(silent=False) or {}))
    return ok({"access_token": token, "user": {"id": str(user.id), "name": user.name, "email": user.email}})
