import uuid

from flask import Blueprint
from flask_jwt_extended import jwt_required

from ...http import current_user_id, read_json_body
from ...responses import ok
from . import service
from .schema import ColumnSchema

columns_bp = Blueprint("columns", __name__)


@columns_bp.post("/boards/<uuid:board_id>/columns")
@jwt_required()
def create_column(board_id: uuid.UUID):
    column = service.create_column(current_user_id(), board_id, read_json_body())
    return ok(ColumnSchema().dump(column), 201)


@columns_bp.patch("/boards/<uuid:board_id>/columns/reorder")
@jwt_required()
def reorder_columns(board_id: uuid.UUID):
    columns = service.reorder_columns(current_user_id(), board_id, read_json_body())
    return ok(ColumnSchema(many=True).dump(columns))


@columns_bp.patch("/columns/<uuid:column_id>")
@jwt_required()
def update_column(column_id: uuid.UUID):
    column = service.update_column(current_user_id(), column_id, read_json_body())
    return ok(ColumnSchema().dump(column))


@columns_bp.delete("/columns/<uuid:column_id>")
@jwt_required()
def delete_column(column_id: uuid.UUID):
    return ok(service.delete_column(current_user_id(), column_id))