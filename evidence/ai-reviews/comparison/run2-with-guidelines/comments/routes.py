import uuid

from flask import Blueprint
from flask_jwt_extended import jwt_required

from ...http import current_user_id, read_json_body
from ...responses import ok
from . import service
from .schema import CommentSchema

comments_bp = Blueprint("comments", __name__)


@comments_bp.post("/cards/<uuid:card_id>/comments")
@jwt_required()
def create_comment(card_id: uuid.UUID):
    comment = service.create_comment(current_user_id(), card_id, read_json_body())
    return ok(CommentSchema().dump(comment), 201)


@comments_bp.get("/cards/<uuid:card_id>/comments")
@jwt_required()
def list_comments(card_id: uuid.UUID):
    return ok(CommentSchema(many=True).dump(service.list_comments(current_user_id(), card_id)))


@comments_bp.patch("/comments/<uuid:comment_id>")
@jwt_required()
def update_comment(comment_id: uuid.UUID):
    comment = service.update_comment(current_user_id(), comment_id, read_json_body())
    return ok(CommentSchema().dump(comment))


@comments_bp.delete("/comments/<uuid:comment_id>")
@jwt_required()
def delete_comment(comment_id: uuid.UUID):
    return ok(service.delete_comment(current_user_id(), comment_id))

