"""GET /api/health: no authentication and no database query (API-003)."""
from flask import Blueprint

from .responses import ok

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health():
    return ok({"status": "ok"})