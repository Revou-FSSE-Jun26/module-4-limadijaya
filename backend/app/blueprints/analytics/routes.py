import uuid

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from ...http import current_user_id
from ...responses import ok
from . import service

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.get("/boards/<uuid:board_id>/analytics")
@jwt_required()
def board_analytics(board_id: uuid.UUID):
    return ok(service.get_analytics(current_user_id(), board_id, request.args))