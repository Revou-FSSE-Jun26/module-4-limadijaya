from flask import request

from app.auth import protected
from app.blueprints.columns import bp
from app.blueprints.columns.schema import ColumnSchema, ReorderSchema
from app.blueprints.columns.service import create, get, remove, reorder, update
from app.responses import ok


def dump(column):
    return {"id": str(column.id), "board_id": str(column.board_id), "name": column.name, "order": column.position, "is_done": column.is_done}


@bp.post("/boards/<uuid:board_id>/columns")
@protected
def create_column(board_id): return ok(dump(create(board_id, ColumnSchema().load(request.get_json() or {}))), 201)


@bp.patch("/columns/<uuid:column_id>")
@protected
def patch_column(column_id): return ok(dump(update(column_id, ColumnSchema().load(request.get_json() or {}))))


@bp.delete("/columns/<uuid:column_id>")
@protected
def delete_column(column_id): remove(column_id); return ok({"id": str(column_id)})


@bp.patch("/boards/<uuid:board_id>/columns/reorder")
@protected
def reorder_columns(board_id): return ok([dump(column) for column in reorder(board_id, ReorderSchema().load(request.get_json() or {}))])
