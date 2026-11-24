from app.auth import protected
from app.blueprints.analytics import bp
from app.blueprints.analytics.service import get
from app.responses import ok


@bp.get("/boards/<uuid:board_id>/analytics")
@protected
def analytics(board_id): return ok(get(board_id))
