"""Boards Blueprint (BOARD-001 to BOARD-007)."""
from sqlalchemy import select

from app.extensions import db
from app.models import BoardColumn, Card
from tests.factories import add_member, auth, make_board, make_card, make_column, make_user


def test_create_board_makes_the_creator_administrator(client, app_context):
    user = make_user()
    response = client.post("/api/boards", json={"name": "  Launch  "}, headers=auth(user))
    assert response.status_code == 201
    board = response.get_json()["data"]
    assert board["name"] == "Launch"
    detail = client.get(f"/api/boards/{board['id']}", headers=auth(user)).get_json()["data"]
    assert detail["role"] == "administrator"


def test_create_board_validation(client, app_context):
    user = make_user()
    assert client.post("/api/boards", json={"name": ""}, headers=auth(user)).status_code == 400
    assert client.post("/api/boards", json={}, headers=auth(user)).status_code == 400
    assert client.post("/api/boards", json={"name": "x", "extra": 1}, headers=auth(user)).status_code == 400


def test_list_boards_returns_only_my_boards(client, app_context):
    me, other = make_user(), make_user()
    mine = make_board(me, "Mine")
    make_board(other, "Theirs")
    response = client.get("/api/boards", headers=auth(me))
    assert [b["id"] for b in response.get_json()["data"]] == [str(mine.id)]


def test_list_boards_empty_is_a_list(client, app_context):
    assert client.get("/api/boards", headers=auth(make_user())).get_json() == {"data": []}


def test_board_detail_nests_live_columns_and_cards_in_order(client, app_context):
    user = make_user()
    board = make_board(user)
    done = make_column(board, "Done", 2048.0)
    todo = make_column(board, "To do", 1024.0)
    make_card(todo, "Second", 2048.0)
    make_card(todo, "First", 1024.0)
    gone = make_card(done, "Hidden", 1024.0)
    gone.deleted_at = gone.created_at
    db.session.commit()
    data = client.get(f"/api/boards/{board.id}", headers=auth(user)).get_json()["data"]
    assert [c["name"] for c in data["columns"]] == ["To do", "Done"]
    assert [c["title"] for c in data["columns"][0]["cards"]] == ["First", "Second"]
    assert data["columns"][1]["cards"] == []
    assert "position" not in data["columns"][0] and data["columns"][0]["order"] == 1024.0
    assert data["members"] == [{"id": str(user.id), "name": user.name}]


def test_non_member_gets_the_same_404_as_a_missing_board(client, app_context):
    owner, stranger = make_user(), make_user()
    board = make_board(owner)
    real = client.get(f"/api/boards/{board.id}", headers=auth(stranger))
    missing = client.get("/api/boards/00000000-0000-4000-8000-000000000009", headers=auth(stranger))
    assert real.status_code == missing.status_code == 404
    assert real.get_json() == missing.get_json()


def test_rename_board_admin_only(client, app_context):
    admin, member = make_user(), make_user()
    board = make_board(admin)
    add_member(board, member)
    assert client.patch(f"/api/boards/{board.id}", json={"name": "New"}, headers=auth(member)).status_code == 403
    ok = client.patch(f"/api/boards/{board.id}", json={"name": "New"}, headers=auth(admin))
    assert ok.status_code == 200 and ok.get_json()["data"]["name"] == "New"
    assert client.patch(f"/api/boards/{board.id}", json={"name": ""}, headers=auth(admin)).status_code == 400


def test_member_gets_403_before_validation(client, app_context):
    admin, member = make_user(), make_user()
    board = make_board(admin)
    add_member(board, member)
    assert client.patch(f"/api/boards/{board.id}", json={"name": ""}, headers=auth(member)).status_code == 403


def test_delete_board_cascades_every_dependent_row(client, app_context):
    admin = make_user()
    board = make_board(admin)
    column = make_column(board)
    card = make_card(column, assignee=admin)
    client.post(f"/api/cards/{card.id}/comments", json={"content": "hello"}, headers=auth(admin))
    response = client.delete(f"/api/boards/{board.id}", headers=auth(admin))
    assert response.status_code == 200
    assert response.get_json() == {"data": {"id": str(board.id)}}
    assert db.session.execute(select(BoardColumn)).first() is None
    assert db.session.execute(select(Card)).first() is None
    from app.models import ActivityEvent, Comment, User

    assert db.session.execute(select(Comment)).first() is None
    assert db.session.execute(select(ActivityEvent)).first() is None
    assert db.session.execute(select(User)).first() is not None


def test_delete_board_member_is_403(client, app_context):
    admin, member = make_user(), make_user()
    board = make_board(admin)
    add_member(board, member)
    assert client.delete(f"/api/boards/{board.id}", headers=auth(member)).status_code == 403


def test_add_member_by_email(client, app_context):
    admin, newcomer = make_user(), make_user(email="new@example.com")
    board = make_board(admin)
    response = client.post(f"/api/boards/{board.id}/members", json={"email": "NEW@example.com"}, headers=auth(admin))
    assert response.status_code == 201
    assert client.get("/api/boards", headers=auth(newcomer)).get_json()["data"][0]["id"] == str(board.id)
    again = client.post(f"/api/boards/{board.id}/members", json={"email": "new@example.com"}, headers=auth(admin))
    assert again.status_code == 409


def test_add_member_rules(client, app_context):
    admin, member = make_user(), make_user()
    board = make_board(admin)
    add_member(board, member)
    body = {"email": "x@example.com"}
    assert client.post(f"/api/boards/{board.id}/members", json=body, headers=auth(member)).status_code == 403
    assert client.post(f"/api/boards/{board.id}/members", json=body, headers=auth(admin)).status_code == 404
    assert client.post(f"/api/boards/{board.id}/members", json={"email": "a@b.co", "role": "administrator"}, headers=auth(admin)).status_code == 400