import uuid

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from ...http import current_user_id, read_json_body
from ...responses import ok
from . import service
from .schema import CardSchema, MyTaskCardSchema

cards_bp = Blueprint("cards", __name__)


@cards_bp.post("/columns/<uuid:column_id>/cards")
@jwt_required()
def create_card(column_id: uuid.UUID):
    card = service.create_card(current_user_id(), column_id, read_json_body())
    return ok(CardSchema().dump(card), 201)


@cards_bp.patch("/cards/<uuid:card_id>")
@jwt_required()
def update_card(card_id: uuid.UUID):
    card = service.update_card(current_user_id(), card_id, read_json_body())
    return ok(CardSchema().dump(card))


@cards_bp.delete("/cards/<uuid:card_id>")
@jwt_required()
def delete_card(card_id: uuid.UUID):
    return ok(service.delete_card(current_user_id(), card_id))


@cards_bp.patch("/cards/<uuid:card_id>/position")
@jwt_required()
def move_card(card_id: uuid.UUID):
    card, rebalanced = service.move_card(current_user_id(), card_id, read_json_body())
    return ok({**CardSchema().dump(card), "rebalanced": rebalanced})


@cards_bp.get("/cards")
@jwt_required()
def my_tasks():
    return ok(MyTaskCardSchema(many=True).dump(service.list_my_tasks(current_user_id(), request.args)))