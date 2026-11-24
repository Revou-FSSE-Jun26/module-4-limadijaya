"""Registers the eight feature Blueprints under /api (BE-02)."""
from flask import Flask

from .analytics import analytics_bp
from .auth import auth_bp
from .boards import boards_bp
from .cards import cards_bp
from .columns import columns_bp
from .comments import comments_bp
from .notifications import notifications_bp
from .users import users_bp


def register_blueprints(app: Flask) -> None:
    for blueprint in (
        auth_bp,
        users_bp,
        boards_bp,
        columns_bp,
        cards_bp,
        comments_bp,
        notifications_bp,
        analytics_bp,
    ):
        app.register_blueprint(blueprint, url_prefix="/api")