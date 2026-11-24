from flask import request

from app.auth import protected
from app.blueprints.comments import bp
from app.blueprints.comments.schema import CommentSchema
from app.blueprints.comments.service import create, list_for_card, remove, update
from app.responses import ok


def dump(value): return {"id": str(value.id), "card_id": str(value.card_id), "author_id": str(value.author_id), "content": value.content}


@bp.post("/cards/<uuid:card_id>/comments")
@protected
def create_comment(card_id): return ok(dump(create(card_id, CommentSchema().load(request.get_json() or {}))), 201)


@bp.get("/cards/<uuid:card_id>/comments")
@protected
def comments(card_id): return ok([dump(value) for value in list_for_card(card_id)])


@bp.patch("/comments/<uuid:comment_id>")
@protected
def patch_comment(comment_id): return ok(dump(update(comment_id, CommentSchema().load(request.get_json() or {}))))


@bp.delete("/comments/<uuid:comment_id>")
@protected
def delete_comment(comment_id): remove(comment_id); return ok({"id": str(comment_id)})
