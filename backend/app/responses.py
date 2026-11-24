"""One response envelope for every endpoint (BE-04, API-001, API-002)."""
from flask import jsonify


def ok(data, status: int = 200):
    """Success envelope: {"data": ...}."""
    return jsonify({"data": data}), status


def fail(message: str, status: int):
    """Error envelope: {"error": "<non-empty string>"}."""
    return jsonify({"error": message}), status
