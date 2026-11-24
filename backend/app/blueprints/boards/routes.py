from flask import request

from app.auth import protected
from app.blueprints.boards import bp
from app.blueprints.boards.schema import BoardSchema, MemberSchema
from app.blueprints.boards.service import add_member, create, delete, dump, get, list_for_user, update
from app.responses import ok


@bp.post("/boards")
@protected
def create_board():
    return ok(dump(create(BoardSchema().load(request.get_json() or {}))), 201)


@bp.get("/boards")
@protected
def list_boards():
    return ok([dump(board) for board in list_for_user()])


@bp.get("/boards/<uuid:board_id>")
@protected
def get_board(board_id):
    return ok(dump(get(board_id), nested=True))


@bp.patch("/boards/<uuid:board_id>")
@protected
def patch_board(board_id):
    return ok(dump(update(board_id, BoardSchema().load(request.get_json() or {}))))


@bp.delete("/boards/<uuid:board_id>")
@protected
def delete_board(board_id):
    delete(board_id)
    return ok({"id": str(board_id)})


@bp.post("/boards/<uuid:board_id>/members")
@protected
def add_board_member(board_id):
    member = add_member(board_id, MemberSchema().load(request.get_json() or {}))
    return ok({"id": str(member.user_id), "role": member.role}, 201)
