"""Flask application factory."""

from __future__ import annotations

from collections.abc import Mapping

from flask import Flask, request

from app.clock import Clock, UtcClock
from app.config import environment_config
from app.extensions import db, jwt, migrate
from app.errors import register_error_handlers


def create_app(config: Mapping[str, object] | None = None) -> Flask:
    """Create and configure the Flask application.

    Tests pass a complete mapping so they do not need production secrets. The
    normal WSGI entry point omits it and therefore reads required values from
    the environment and fails fast when one is missing.
    """

    app = Flask(__name__)
    app.config.from_mapping(environment_config() if config is None else dict(config))
    app.extensions["clock"] = app.config.get("CLOCK", UtcClock())

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    register_error_handlers(app)

    @app.after_request
    def add_local_cors(response):
        origin = request.headers.get("Origin")
        if origin and origin == app.config.get("FRONTEND_ORIGIN"):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PATCH, DELETE, OPTIONS"
            response.headers["Vary"] = "Origin"
        return response

    from app.blueprints.analytics import bp as analytics_bp
    from app.blueprints.auth import bp as auth_bp
    from app.blueprints.boards import bp as boards_bp
    from app.blueprints.cards import bp as cards_bp
    from app.blueprints.columns import bp as columns_bp
    from app.blueprints.comments import bp as comments_bp
    from app.blueprints.notifications import bp as notifications_bp
    from app.blueprints.users import bp as users_bp

    for blueprint in (auth_bp, users_bp, boards_bp, columns_bp, cards_bp, comments_bp, notifications_bp, analytics_bp):
        app.register_blueprint(blueprint, url_prefix="/api")

    @app.get("/api/health")
    def health():
        return {"data": {"status": "ok"}}, 200

    # Import model modules so Flask-Migrate sees all approved tables.
    from app import models  # noqa: F401

    return app


def get_clock(app: Flask) -> Clock:
    """Return the injectable application clock."""

    return app.extensions["clock"]


__all__ = ["create_app", "db", "get_clock", "jwt", "migrate"]
