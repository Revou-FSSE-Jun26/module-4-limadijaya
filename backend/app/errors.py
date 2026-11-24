from flask import Flask
from marshmallow import ValidationError
from werkzeug.exceptions import HTTPException, MethodNotAllowed, NotFound, RequestEntityTooLarge

from app.responses import fail
from app.extensions import db


class NotFoundError(Exception):
    pass


class ForbiddenError(Exception):
    pass


class ConflictError(Exception):
    pass


def register_error_handlers(app: Flask):
    @app.errorhandler(NotFoundError)
    def not_found_error(_):
        return fail("Resource not found.", 404)

    @app.errorhandler(ForbiddenError)
    def forbidden_error(_):
        return fail("You do not have permission to perform this action.", 403)

    @app.errorhandler(ConflictError)
    def conflict_error(error):
        return fail(str(error), 409)

    @app.errorhandler(ValidationError)
    def validation_error(error):
        message = next(iter(error.messages.values())) if error.messages else "Invalid request."
        if isinstance(message, list):
            message = message[0]
        return fail(f"Invalid request: {message}.", 400)

    @app.errorhandler(RequestEntityTooLarge)
    def too_large(_):
        return fail("Request body is too large.", 413)

    @app.errorhandler(MethodNotAllowed)
    def method_not_allowed(_):
        return fail("Method not allowed.", 405)

    @app.errorhandler(NotFound)
    def route_not_found(_):
        return fail("Resource not found.", 404)

    @app.errorhandler(HTTPException)
    def http_error(error):
        return fail(error.description or "Request failed.", error.code or 400)

    @app.errorhandler(Exception)
    def unhandled(_):
        db.session.rollback()
        return fail("Internal server error.", 500)
