"""Auth and users Blueprints (AUTH-001 to AUTH-003, USER-001, USER-002)."""
from flask_jwt_extended import decode_token

from tests.factories import PASSWORD, auth, make_user


def register(client, **overrides):
    body = {"name": "Alice", "email": "Alice@Example.com ", "password": PASSWORD}
    body.update(overrides)
    return client.post("/api/auth/register", json=body)


def test_register_returns_201_without_password_data(client):
    response = register(client)
    assert response.status_code == 201
    data = response.get_json()["data"]
    assert set(data) == {"id", "name", "email"}
    assert data["email"] == "alice@example.com"  # trimmed and lowercased (DA-06)


def test_register_stores_a_hash_not_the_password(client, app_context):
    from sqlalchemy import select

    from app.extensions import db
    from app.models import User

    register(client)
    user = db.session.execute(select(User)).scalar_one()
    assert user.password_hash != PASSWORD
    assert user.password_hash.startswith("scrypt:")


def test_register_duplicate_email_is_409_case_insensitive(client):
    register(client)
    response = register(client, email="ALICE@example.com")
    assert response.status_code == 409
    assert isinstance(response.get_json()["error"], str)


def test_register_validation_errors_are_400(client):
    assert register(client, name="  ").status_code == 400
    assert register(client, email="not-an-email").status_code == 400
    assert register(client, password="").status_code == 400
    assert client.post("/api/auth/register", json={"name": "A"}).status_code == 400
    assert register(client, role="administrator").status_code == 400  # unknown key


def test_error_does_not_echo_the_password(client):
    response = register(client, email="bad", password="SuperSecretValue!")
    assert "SuperSecretValue" not in response.get_data(as_text=True)


def test_login_returns_a_token_with_expiry(client, app_context):
    register(client)
    response = client.post("/api/auth/login", json={"email": "alice@example.com", "password": PASSWORD})
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert set(data) == {"access_token"}
    claims = decode_token(data["access_token"])
    assert "exp" in claims and claims["exp"] > claims["iat"]


def test_login_failures_share_one_401_body(client):
    register(client)
    wrong = client.post("/api/auth/login", json={"email": "alice@example.com", "password": "nope"})
    unknown = client.post("/api/auth/login", json={"email": "ghost@example.com", "password": "nope"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.get_json() == unknown.get_json() == {"error": "Invalid email or password."}


def test_login_missing_field_is_400(client):
    assert client.post("/api/auth/login", json={"email": "a@b.co"}).status_code == 400


def test_no_refresh_route_exists(client):
    assert client.post("/api/auth/refresh").status_code == 404


def test_get_me_excludes_password(client, app_context):
    user = make_user("Bob", "bob@example.com")
    response = client.get("/api/users/me", headers=auth(user))
    assert response.status_code == 200
    assert response.get_json()["data"] == {"id": str(user.id), "name": "Bob", "email": "bob@example.com"}


def test_patch_me_updates_name_and_email(client, app_context):
    user = make_user("Bob", "bob@example.com")
    response = client.patch("/api/users/me", json={"name": " Robert ", "email": "ROBERT@example.com"}, headers=auth(user))
    assert response.status_code == 200
    assert response.get_json()["data"]["name"] == "Robert"
    assert response.get_json()["data"]["email"] == "robert@example.com"


def test_patch_me_rejects_password_and_empty_body(client, app_context):
    user = make_user()
    assert client.patch("/api/users/me", json={"password": "x"}, headers=auth(user)).status_code == 400
    assert client.patch("/api/users/me", json={}, headers=auth(user)).status_code == 400


def test_patch_me_duplicate_email_is_409(client, app_context):
    first = make_user(email="first@example.com")
    second = make_user(email="second@example.com")
    response = client.patch("/api/users/me", json={"email": first.email}, headers=auth(second))
    assert response.status_code == 409