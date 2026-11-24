"""Application factory (BE-01)."""
from __future__ import annotations

import logging
import time
import uuid as uuid_module

from flask import Flask, g, request
from flask_cors import CORS

from .config import build_config
from .errors import register_error_handlers, register_jwt_callbacks
from .extensions import db, jwt, migrate


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(build_config(config))

    logging.basicConfig(level=app.config["LOG_LEVEL"], format="%(asctime)s %(levelname)s %(message)s")

    # Importing the models registers all eight tables with Flask-Migrate.
    from . import models  # noqa: F401

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # CORS applies to the health route only (BE-19, API-004).
    CORS(
        app,
        resources={r"/api/health": {"origins": [app.config["FRONTEND_ORIGIN"]], "methods": ["GET"]}},
        supports_credentials=False,
    )

    register_jwt_callbacks()
    register_error_handlers(app)

    from .blueprints import register_blueprints
    from .health import health_bp

    register_blueprints(app)
    app.register_blueprint(health_bp, url_prefix="/api")

    @app.before_request
    def _start_timer():
        g.request_id = uuid_module.uuid4().hex[:8]
        g.started = time.perf_counter()

    @app.after_request
    def _log_request(response):
        # Never log headers, bodies, tokens, or the database URL (design 4.12).
        duration_ms = (time.perf_counter() - g.get("started", time.perf_counter())) * 1000
        app.logger.info(
            "%s %s %s %s %.1fms", g.get("request_id", "-"), request.method, request.path, response.status_code, duration_ms
        )
        return response

    return app