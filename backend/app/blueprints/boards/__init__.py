from flask import Blueprint

bp = Blueprint("boards", __name__)
from . import routes  # noqa: E402,F401
