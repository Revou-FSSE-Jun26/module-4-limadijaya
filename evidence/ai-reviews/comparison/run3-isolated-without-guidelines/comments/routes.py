import uuid
from functools import wraps

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from marshmallow import ValidationError

from .schema import comment_input_schema
from .service import (
    ServiceError,
    create_comment,
    delete_comment,
    list_comments,
    update_comment,
)

comments_bp = Blueprint("comments", __name__)


def _error(message, status):
    return jsonify({"error": message}), status


def auth_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            user_id = uuid.UUID(str(get_jwt_identity()))
        except Exception:
            return _error("authentication required", 401)
        return fn(user_id, *args, **kwargs)

    return wrapper


def _content_from_body():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        raise ServiceError("invalid request body", 400)
    try:
        data = comment_input_schema.load(body)
    except ValidationError as exc:
        messages = exc.messages
        detail = "; ".join(
            f"{field}: {', '.join(msgs)}" for field, msgs in messages.items()
        ) if isinstance(messages, dict) else "invalid request body"
        raise ServiceError(detail, 400)
    return data["content"]


def _handle(fn):
    try:
        return fn()
    except ServiceError as exc:
        return _error(exc.message, exc.status)


@comments_bp.post("/api/cards/<card_id>/comments")
@auth_required
def post_comment(user_id, card_id):
    def run():
        content = _content_from_body()
        return jsonify({"data": create_comment(card_id, user_id, content)}), 201

    return _handle(run)


@comments_bp.get("/api/cards/<card_id>/comments")
@auth_required
def get_comments(user_id, card_id):
    return _handle(lambda: (jsonify({"data": list_comments(card_id, user_id)}), 200))


@comments_bp.patch("/api/comments/<comment_id>")
@auth_required
def patch_comment(user_id, comment_id):
    def run():
        content = _content_from_body()
        return jsonify({"data": update_comment(comment_id, user_id, content)}), 200

    return _handle(run)


@comments_bp.delete("/api/comments/<comment_id>")
@auth_required
def remove_comment(user_id, comment_id):
    return _handle(
        lambda: (jsonify({"data": delete_comment(comment_id, user_id)}), 200)
    )
