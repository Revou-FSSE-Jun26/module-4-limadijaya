"""Request helpers that routes may use. Routes never run queries or commits (BE-03)."""
from __future__ import annotations

import json
import uuid

from flask import request
from flask_jwt_extended import get_jwt_identity
from werkzeug.exceptions import UnsupportedMediaType

from .errors import BadRequestError


def _reject_constant(name: str):
    raise ValueError(f"Invalid JSON constant {name}")


def read_json_body():
    """Return the parsed JSON body, or raise 415 / 400. NaN and Infinity are rejected."""
    if request.mimetype != "application/json":
        raise UnsupportedMediaType()
    try:
        return json.loads(request.get_data(), parse_constant=_reject_constant)
    except (ValueError, UnicodeDecodeError):
        raise BadRequestError("Invalid request: the body is not valid JSON.") from None


def current_user_id() -> uuid.UUID:
    return uuid.UUID(get_jwt_identity())
