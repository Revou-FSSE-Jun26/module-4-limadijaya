import uuid

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.responses import ok

from . import service
from .schema import CommentSchema

comments_bp = Blueprint("comments", __name__)


def _current_user_id():
    return uuid.UUID(str(get_jwt_identity()))


@comments_bp.post("/cards/<uuid:card_id>/comments")
@jwt_required()
def create_comment(card_id):
    raw = request.get_json()  # invalid JSON -> 400, wrong content type -> 415
    comment = service.create_comment(_current_user_id(), card_id, raw)
    return ok(CommentSchema().dump(comment), 201)


@comments_bp.get("/cards/<uuid:card_id>/comments")
@jwt_required()
def list_comments(card_id):
    comments = service.list_comments(_current_user_id(), card_id)
    return ok(CommentSchema(many=True).dump(comments))


@comments_bp.patch("/comments/<uuid:comment_id>")
@jwt_required()
def update_comment(comment_id):
    raw = request.get_json()
    comment = service.update_comment(_current_user_id(), comment_id, raw)
    return ok(CommentSchema().dump(comment))


@comments_bp.delete("/comments/<uuid:comment_id>")
@jwt_required()
def delete_comment(comment_id):
    result = service.delete_comment(_current_user_id(), comment_id)
    return ok({"id": str(result["id"])})
