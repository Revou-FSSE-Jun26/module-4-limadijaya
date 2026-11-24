import uuid

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from ...http import current_user_id
from ...responses import ok
from . import service

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.get("/notifications")
@jwt_required()
def list_notifications():
    return ok(service.list_notifications(current_user_id(), request.args))


@notifications_bp.patch("/notifications/<uuid:notification_id>/read")
@jwt_required()
def mark_read(notification_id: uuid.UUID):
    return ok(service.mark_read(current_user_id(), notification_id))