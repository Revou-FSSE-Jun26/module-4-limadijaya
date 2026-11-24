"""Error classes and the central error handlers (BE-05, API-002).

Every error body is {"error": "<non-empty string>"}. The text never carries a stack
trace, a SQL statement, a path, or a submitted value.
"""
from __future__ import annotations

import logging

from flask import Flask
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import (
    HTTPException,
    MethodNotAllowed,
    NotFound,
    RequestEntityTooLarge,
    UnsupportedMediaType,
)

from .extensions import db, jwt
from .responses import fail

logger = logging.getLogger(__name__)

NOT_FOUND_MESSAGE = "Resource not found."
FORBIDDEN_MESSAGE = "You do not have permission to perform this action."
AUTH_REQUIRED_MESSAGE = "Authentication required."


class ApiError(Exception):
    status = 500
    default_message = "Internal server error."

    def __init__(self, message: str | None = None):
        super().__init__(message or self.default_message)
        self.message = message or self.default_message


class BadRequestError(ApiError):
    status = 400
    default_message = "Invalid request."


class AuthenticationError(ApiError):
    status = 401
    default_message = "Invalid email or password."


class ForbiddenError(ApiError):
    status = 403
    default_message = FORBIDDEN_MESSAGE


class NotFoundError(ApiError):
    status = 404
    default_message = NOT_FOUND_MESSAGE


class ConflictError(ApiError):
    status = 409
    default_message = "The request conflicts with the current state."


def validation_message(error: ValidationError) -> str:
    """Summarize the first validation problem without echoing any submitted value."""
    messages = error.messages
    path: list[str] = []
    while isinstance(messages, dict) and messages:
        key, messages = next(iter(messages.items()))
        path.append(str(key))
    while isinstance(messages, list) and messages and isinstance(messages[0], (dict, list)):
        messages = messages[0]
        if isinstance(messages, dict) and messages:
            key, messages = next(iter(messages.items()))
            path.append(str(key))
    detail = messages[0] if isinstance(messages, list) and messages else "is invalid"
    detail = str(detail).rstrip(".")
    field = ".".join(p for p in path if p != "_schema")
    if field:
        return f"Invalid request: {field}: {detail}."
    return f"Invalid request: {detail}."


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ApiError)
    def handle_api_error(error: ApiError):
        db.session.rollback()
        return fail(error.message, error.status)

    @app.errorhandler(ValidationError)
    def handle_validation(error: ValidationError):
        db.session.rollback()
        return fail(validation_message(error), 400)

    @app.errorhandler(IntegrityError)
    def handle_integrity(error: IntegrityError):
        db.session.rollback()
        logger.warning("Integrity error converted to 409")
        return fail("The request conflicts with the current state.", 409)

    @app.errorhandler(NotFound)
    def handle_not_found(_error):
        return fail(NOT_FOUND_MESSAGE, 404)

    @app.errorhandler(MethodNotAllowed)
    def handle_method_not_allowed(_error):
        return fail("Method not allowed.", 405)

    @app.errorhandler(UnsupportedMediaType)
    def handle_unsupported(_error):
        return fail("Content-Type must be application/json.", 415)

    @app.errorhandler(RequestEntityTooLarge)
    def handle_too_large(_error):
        return fail("Request body is too large.", 413)

    @app.errorhandler(HTTPException)
    def handle_http(error: HTTPException):
        status = error.code or 500
        if status >= 500:
            return fail("Internal server error.", status)
        return fail("Invalid request.", status)

    @app.errorhandler(Exception)
    def handle_unexpected(error: Exception):
        db.session.rollback()
        logger.error("Unhandled exception", exc_info=error)
        return fail("Internal server error.", 500)


def register_jwt_callbacks() -> None:
    """Flask-JWT-Extended answers some bad tokens with 422. The API contract says 401 (AUTH-003)."""

    @jwt.unauthorized_loader
    def missing_token(_reason):
        return fail(AUTH_REQUIRED_MESSAGE, 401)

    @jwt.invalid_token_loader
    def invalid_token(_reason):
        return fail(AUTH_REQUIRED_MESSAGE, 401)

    @jwt.expired_token_loader
    def expired_token(_header, _payload):
        return fail(AUTH_REQUIRED_MESSAGE, 401)

    @jwt.revoked_token_loader
    def revoked_token(_header, _payload):
        return fail(AUTH_REQUIRED_MESSAGE, 401)

    @jwt.needs_fresh_token_loader
    def needs_fresh(_header, _payload):
        return fail(AUTH_REQUIRED_MESSAGE, 401)
