from flask import request

from app.auth import protected
from app.blueprints.cards import bp
from app.blueprints.cards.schema import CardPositionSchema, CardSchema
from app.blueprints.cards.service import assigned, create, get, move, remove, update
from app.responses import ok


def dump(card):
    return {"id": str(card.id), "column_id": str(card.column_id), "title": card.title, "order": card.position, "assignee_id": str(card.assignee_id) if card.assignee_id else None}


@bp.post("/columns/<uuid:column_id>/cards")
@protected
def create_card(column_id): return ok(dump(create(column_id, CardSchema().load(request.get_json() or {}))), 201)


@bp.patch("/cards/<uuid:card_id>")
@protected
def patch_card(card_id): return ok(dump(update(card_id, CardSchema().load(request.get_json() or {}))))


@bp.delete("/cards/<uuid:card_id>")
@protected
def delete_card(card_id): remove(card_id); return ok({"id": str(card_id)})


@bp.patch("/cards/<uuid:card_id>/position")
@protected
def move_card(card_id): return ok(dump(move(card_id, CardPositionSchema().load(request.get_json() or {}))))


@bp.get("/cards")
@protected
def assigned_cards(): return ok([dump(card) for card in assigned()])
