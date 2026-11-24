from flask import request

from app.auth import protected
from app.blueprints.notifications import bp
from app.blueprints.notifications.schema import PaginationSchema
from app.blueprints.notifications.service import list_for_user, mark_read
from app.responses import ok


def dump(value): return {"id": str(value.id), "type": value.type, "message": value.message, "is_read": value.is_read, "card_id": str(value.card_id), "board_id": str(value.board_id)}


@bp.get("/notifications")
@protected
def notifications():
    query = PaginationSchema().load(request.args.to_dict())
    return ok([dump(value) for value in list_for_user(query["page"], query["per_page"])])


@bp.patch("/notifications/<uuid:notification_id>/read")
@protected
def read_notification(notification_id): return ok(dump(mark_read(notification_id)))
