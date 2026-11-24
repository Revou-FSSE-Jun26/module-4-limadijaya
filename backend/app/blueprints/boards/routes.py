import uuid

from flask import Blueprint
from flask_jwt_extended import jwt_required

from ...http import current_user_id, read_json_body
from ...responses import ok
from ..users.schema import UserSchema
from . import service
from .schema import BoardSummarySchema

boards_bp = Blueprint("boards", __name__)


@boards_bp.post("/boards")
@jwt_required()
def create_board():
    board = service.create_board(current_user_id(), read_json_body())
    return ok(BoardSummarySchema().dump(board), 201)


@boards_bp.get("/boards")
@jwt_required()
def list_boards():
    return ok(BoardSummarySchema(many=True).dump(service.list_boards(current_user_id())))


@boards_bp.get("/boards/<uuid:board_id>")
@jwt_required()
def get_board(board_id: uuid.UUID):
    return ok(service.get_board_detail(current_user_id(), board_id))


@boards_bp.patch("/boards/<uuid:board_id>")
@jwt_required()
def update_board(board_id: uuid.UUID):
    board = service.update_board(current_user_id(), board_id, read_json_body())
    return ok(BoardSummarySchema().dump(board))


@boards_bp.delete("/boards/<uuid:board_id>")
@jwt_required()
def delete_board(board_id: uuid.UUID):
    return ok(service.delete_board(current_user_id(), board_id))


@boards_bp.post("/boards/<uuid:board_id>/members")
@jwt_required()
def add_member(board_id: uuid.UUID):
    user = service.add_member(current_user_id(), board_id, read_json_body())
    return ok(UserSchema().dump(user), 201)