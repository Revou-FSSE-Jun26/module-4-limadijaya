"""Columns Blueprint (COLUMN-001 to COLUMN-005)."""
from sqlalchemy import select

from app.extensions import db
from app.models import Card
from tests.factories import add_member, auth, make_board, make_card, make_column, make_user


def setup_board():
    admin, member = make_user(), make_user()
    board = make_board(admin)
    add_member(board, member)
    return admin, member, board


def test_create_column_appends_with_float_order(client, app_context):
    admin, _member, board = setup_board()
    first = client.post(f"/api/boards/{board.id}/columns", json={"name": "To do"}, headers=auth(admin))
    second = client.post(f"/api/boards/{board.id}/columns", json={"name": "Doing"}, headers=auth(admin))
    assert first.status_code == second.status_code == 201
    assert first.get_json()["data"]["order"] == 1024.0
    assert second.get_json()["data"]["order"] == 2048.0
    assert first.get_json()["data"]["is_done"] is False
    assert "position" not in first.get_json()["data"]


def test_create_column_errors(client, app_context):
    admin, _member, board = setup_board()
    stranger = make_user()
    assert client.post(f"/api/boards/{board.id}/columns", json={"name": ""}, headers=auth(admin)).status_code == 400
    assert client.post(f"/api/boards/{board.id}/columns", json={"name": "x"}, headers=auth(stranger)).status_code == 404


def test_rename_column_by_member_and_is_done_admin_only(client, app_context):
    admin, member, board = setup_board()
    column = make_column(board)
    assert client.patch(f"/api/columns/{column.id}", json={"name": "Backlog"}, headers=auth(member)).status_code == 200
    forbidden = client.patch(f"/api/columns/{column.id}", json={"is_done": False}, headers=auth(member))
    assert forbidden.status_code == 403
    mixed = client.patch(f"/api/columns/{column.id}", json={"name": "Z", "is_done": True}, headers=auth(member))
    assert mixed.status_code == 403
    assert client.patch(f"/api/columns/{column.id}", json={"is_done": "true"}, headers=auth(admin)).status_code == 400
    ok = client.patch(f"/api/columns/{column.id}", json={"is_done": True}, headers=auth(admin))
    assert ok.status_code == 200 and ok.get_json()["data"]["is_done"] is True


def test_toggling_is_done_stamps_and_clears_completed_at(client, app_context):
    admin, _member, board = setup_board()
    column = make_column(board)
    card = make_card(column)
    client.patch(f"/api/columns/{column.id}", json={"is_done": True}, headers=auth(admin))
    db.session.expire_all()
    assert db.session.get(Card, card.id).completed_at is not None
    client.patch(f"/api/columns/{column.id}", json={"is_done": False}, headers=auth(admin))
    db.session.expire_all()
    assert db.session.get(Card, card.id).completed_at is None


def test_delete_column_is_admin_only_and_soft_deletes_cards(client, app_context):
    admin, member, board = setup_board()
    column = make_column(board)
    card = make_card(column)
    assert client.delete(f"/api/columns/{column.id}", headers=auth(member)).status_code == 403
    response = client.delete(f"/api/columns/{column.id}", headers=auth(admin))
    assert response.status_code == 200
    db.session.expire_all()
    row = db.session.get(Card, card.id)
    assert row is not None and row.deleted_at is not None and row.column_id == column.id
    assert client.delete(f"/api/columns/{column.id}", headers=auth(member)).status_code == 404
    detail = client.get(f"/api/boards/{board.id}", headers=auth(admin)).get_json()["data"]
    assert detail["columns"] == []


def test_reorder_applies_new_float_orders(client, app_context):
    admin, member, board = setup_board()
    a, b, c = make_column(board, "A", 1024.0), make_column(board, "B", 2048.0), make_column(board, "C", 3072.0)
    body = {"columns": [{"id": str(c.id), "order": 512.5}]}
    response = client.patch(f"/api/boards/{board.id}/columns/reorder", json=body, headers=auth(member))
    assert response.status_code == 200
    assert [col["name"] for col in response.get_json()["data"]] == ["C", "A", "B"]
    assert response.get_json()["data"][0]["order"] == 512.5


def test_reorder_swap_is_allowed_but_collision_is_409(client, app_context):
    admin, _member, board = setup_board()
    a, b = make_column(board, "A", 1024.0), make_column(board, "B", 2048.0)
    swap = {"columns": [{"id": str(a.id), "order": 2048.0}, {"id": str(b.id), "order": 1024.0}]}
    assert client.patch(f"/api/boards/{board.id}/columns/reorder", json=swap, headers=auth(admin)).status_code == 200
    collide = {"columns": [{"id": str(a.id), "order": 2048.0}]}
    # a is now 2048.0, so submitting 1024.0 for it would collide with b.
    collide = {"columns": [{"id": str(a.id), "order": 1024.0}]}
    assert client.patch(f"/api/boards/{board.id}/columns/reorder", json=collide, headers=auth(admin)).status_code == 409


def test_reorder_validation(client, app_context):
    admin, _member, board = setup_board()
    other_board = make_board(admin, "Other")
    foreign = make_column(other_board)
    mine = make_column(board)
    url = f"/api/boards/{board.id}/columns/reorder"
    assert client.patch(url, json={"columns": []}, headers=auth(admin)).status_code == 400
    assert client.patch(url, json={"columns": [{"id": str(foreign.id), "order": 5}]}, headers=auth(admin)).status_code == 400
    for bad in (0, -1, True, "5", None):
        body = {"columns": [{"id": str(mine.id), "order": bad}]}
        assert client.patch(url, json=body, headers=auth(admin)).status_code == 400, bad
    body = {"columns": [{"id": str(mine.id), "position": 5}]}
    assert client.patch(url, json=body, headers=auth(admin)).status_code == 400