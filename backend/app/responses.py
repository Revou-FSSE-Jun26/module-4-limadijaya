from flask import jsonify


def ok(data, status=200):
    return jsonify({"data": data}), status


def fail(message, status):
    return jsonify({"error": str(message)}), status
