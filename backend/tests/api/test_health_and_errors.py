"""Health route, response envelope, and central error handlers (API-001 to API-004)."""
import pytest

from tests.factories import auth, make_user

PROTECTED = [
    ("get", "/api/users/me"),
    ("patch", "/api/users/me"),
    ("post", "/api/boards"),
    ("get", "/api/boards"),
    ("get", "/api/boards/00000000-0000-4000-8000-000000000001"),
    ("patch", "/api/boards/00000000-0000-4000-8000-000000000001"),
    ("delete", "/api/boards/00000000-0000-4000-8000-000000000001"),
    ("post", "/api/boards/00000000-0000-4000-8000-000000000001/members"),
    ("post", "/api/boards/00000000-0000-4000-8000-000000000001/columns"),
    ("patch", "/api/boards/00000000-0000-4000-8000-000000000001/columns/reorder"),
    ("patch", "/api/columns/00000000-0000-4000-8000-000000000001"),
    ("delete", "/api/columns/00000000-0000-4000-8000-000000000001"),
    ("post", "/api/columns/00000000-0000-4000-8000-000000000001/cards"),
    ("patch", "/api/cards/00000000-0000-4000-8000-000000000001"),
    ("delete", "/api/cards/00000000-0000-4000-8000-000000000001"),
    ("patch", "/api/cards/00000000-0000-4000-8000-000000000001/position"),
    ("get", "/api/cards?assignee=me"),
    ("post", "/api/cards/00000000-0000-4000-8000-000000000001/comments"),
    ("get", "/api/cards/00000000-0000-4000-8000-000000000001/comments"),
    ("patch", "/api/comments/00000000-0000-4000-8000-000000000001"),
    ("delete", "/api/comments/00000000-0000-4000-8000-000000000001"),
    ("get", "/api/notifications"),
    ("patch", "/api/notifications/00000000-0000-4000-8000-000000000001/read"),
    ("get", "/api/boards/00000000-0000-4000-8000-000000000001/analytics"),
]


def test_health_returns_ok_envelope(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json() == {"data": {"status": "ok"}}


def test_health_cors_allows_only_the_frontend_origin(client):
    allowed = client.get("/api/health", headers={"Origin": "http://localhost:3000"})
    assert allowed.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"
    assert "Access-Control-Allow-Credentials" not in allowed.headers
    other = client.get("/api/health", headers={"Origin": "https://evil.example"})
    assert "Access-Control-Allow-Origin" not in other.headers


def test_no_cors_headers_on_other_routes(client):
    response = client.get("/api/boards", headers={"Origin": "http://localhost:3000"})
    assert "Access-Control-Allow-Origin" not in response.headers


@pytest.mark.parametrize("method,path", PROTECTED)
def test_every_protected_route_rejects_a_missing_token(client, method, path):
    response = getattr(client, method)(path)
    assert response.status_code == 401
    assert response.get_json() == {"error": "Authentication required."}


def test_garbage_token_is_401_not_422(client):
    response = client.get("/api/boards", headers={"Authorization": "Bearer not-a-token"})
    assert response.status_code == 401
    assert isinstance(response.get_json()["error"], str)


def test_unknown_route_is_404_envelope(client):
    response = client.get("/api/nope")
    assert response.status_code == 404
    assert response.get_json() == {"error": "Resource not found."}


def test_wrong_method_is_405_envelope(client):
    response = client.delete("/api/health")
    assert response.status_code == 405
    assert response.get_json() == {"error": "Method not allowed."}


def test_non_uuid_path_id_is_404(client, app_context):
    user = make_user()
    response = client.get("/api/boards/not-a-uuid", headers=auth(user))
    assert response.status_code == 404


def test_wrong_content_type_is_415(client, app_context):
    user = make_user()
    response = client.post("/api/boards", data="name=x", headers=auth(user))
    assert response.status_code == 415


def test_invalid_json_is_400(client, app_context):
    user = make_user()
    response = client.post("/api/boards", data="{bad", content_type="application/json", headers=auth(user))
    assert response.status_code == 400
    assert isinstance(response.get_json()["error"], str)


def test_nan_constant_is_rejected(client, app_context):
    user = make_user()
    response = client.post(
        "/api/boards", data='{"name": NaN}', content_type="application/json", headers=auth(user)
    )
    assert response.status_code == 400


def test_oversized_body_is_413(client, app_context):
    user = make_user()
    big = '{"name": "' + "a" * 1_100_000 + '"}'
    response = client.post("/api/boards", data=big, content_type="application/json", headers=auth(user))
    assert response.status_code == 413
    assert response.get_json() == {"error": "Request body is too large."}