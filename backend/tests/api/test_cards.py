"""Cards Blueprint (CARD-001 to CARD-007), including CardPositionSchema validation."""
from sqlalchemy import select

from app.extensions import db
from app.models import ActivityEvent, Card, Notification
from tests.factories import add_member, auth, make_board, make_card, make_column, make_user


def setup_board():
    admin, member = make_user("Ada Admin"), make_user("Mia Member")
    board = make_board(admin)
    add_member(board, member)
    return admin, member, board


def test_create_card_appends_and_records_an_event(client, app_context):
    admin, _member, board = setup_board()
    column = make_column(board)
    first = client.post(f"/api/columns/{column.id}/cards", json={"title": " Draft "}, headers=auth(admin))
    second = client.post(f"/api/columns/{column.id}/cards", json={"title": "Review"}, headers=auth(admin))
    assert first.status_code == 201
    card = first.get_json()["data"]
    assert card["title"] == "Draft" and card["order"] == 1024.0 and card["assignee_id"] is None
    assert second.get_json()["data"]["order"] == 2048.0
    events = db.session.execute(select(ActivityEvent)).scalars().all()
    assert [e.type for e in events] == ["card_created", "card_created"]


def test_create_card_in_done_column_is_completed(client, app_context):
    admin, _member, board = setup_board()
    column = make_column(board, is_done=True)
    card = client.post(f"/api/columns/{column.id}/cards", json={"title": "x"}, headers=auth(admin)).get_json()["data"]
    assert card["completed_at"] is not None


def test_create_card_errors(client, app_context):
    admin, _member, board = setup_board()
    column = make_column(board)
    stranger = make_user()
    url = f"/api/columns/{column.id}/cards"
    assert client.post(url, json={"title": ""}, headers=auth(admin)).status_code == 400
    assert client.post(url, json={"title": "x", "assignee_id": str(admin.id)}, headers=auth(admin)).status_code == 400
    assert client.post(url, json={"title": "x"}, headers=auth(stranger)).status_code == 404


def test_update_title_and_assignment_creates_one_notification(client, app_context):
    admin, member, board = setup_board()
    card = make_card(make_column(board))
    url = f"/api/cards/{card.id}"
    response = client.patch(url, json={"title": "New", "assignee_id": str(member.id)}, headers=auth(admin))
    assert response.status_code == 200 and response.get_json()["data"]["assignee_id"] == str(member.id)
    notes = db.session.execute(select(Notification)).scalars().all()
    assert len(notes) == 1 and notes[0].user_id == member.id and notes[0].type == "card_assigned"
    assert "Ada Admin" in notes[0].message and "New" in notes[0].message
    # Same assignee again is a no-op: no second notification.
    client.patch(url, json={"assignee_id": str(member.id)}, headers=auth(admin))
    assert len(db.session.execute(select(Notification)).scalars().all()) == 1


def test_self_assignment_and_unassignment_do_not_notify(client, app_context):
    admin, member, board = setup_board()
    card = make_card(make_column(board))
    client.patch(f"/api/cards/{card.id}", json={"assignee_id": str(admin.id)}, headers=auth(admin))
    client.patch(f"/api/cards/{card.id}", json={"assignee_id": None}, headers=auth(admin))
    assert db.session.execute(select(Notification)).first() is None


def test_update_card_validation(client, app_context):
    admin, _member, board = setup_board()
    outsider = make_user()
    card = make_card(make_column(board))
    url = f"/api/cards/{card.id}"
    assert client.patch(url, json={}, headers=auth(admin)).status_code == 400
    assert client.patch(url, json={"title": ""}, headers=auth(admin)).status_code == 400
    assert client.patch(url, json={"assignee_id": "nope"}, headers=auth(admin)).status_code == 400
    assert client.patch(url, json={"assignee_id": str(outsider.id)}, headers=auth(admin)).status_code == 400
    assert client.patch(url, json={"id": str(card.id)}, headers=auth(admin)).status_code == 400


def test_delete_card_is_a_soft_delete(client, app_context):
    admin, _member, board = setup_board()
    card = make_card(make_column(board))
    response = client.delete(f"/api/cards/{card.id}", headers=auth(admin))
    assert response.status_code == 200 and response.get_json() == {"data": {"id": str(card.id)}}
    db.session.expire_all()
    assert db.session.get(Card, card.id).deleted_at is not None
    assert client.delete(f"/api/cards/{card.id}", headers=auth(admin)).status_code == 404


def test_move_card_between_columns_with_float_order(client, app_context):
    admin, _member, board = setup_board()
    source, target = make_column(board, "A", 1024.0), make_column(board, "B", 2048.0)
    card = make_card(source)
    make_card(target, "Existing", 1024.0)
    response = client.patch(
        f"/api/cards/{card.id}/position", json={"column_id": str(target.id), "order": 512.25}, headers=auth(admin)
    )
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["column_id"] == str(target.id) and data["order"] == 512.25 and data["rebalanced"] is False
    assert "position" not in data
    moved = db.session.execute(select(ActivityEvent).where(ActivityEvent.type == "card_moved")).scalar_one()
    assert moved.from_column_id == source.id and moved.to_column_id == target.id


def test_move_to_done_column_sets_completed_at_and_back_clears_it(client, app_context):
    admin, _member, board = setup_board()
    todo, done = make_column(board, "To do", 1024.0), make_column(board, "Done", 2048.0, is_done=True)
    card = make_card(todo)
    moved = client.patch(f"/api/cards/{card.id}/position", json={"column_id": str(done.id), "order": 1024}, headers=auth(admin))
    assert moved.get_json()["data"]["completed_at"] is not None
    back = client.patch(f"/api/cards/{card.id}/position", json={"column_id": str(todo.id), "order": 1024}, headers=auth(admin))
    assert back.get_json()["data"]["completed_at"] is None


def test_move_tie_rebalances_the_destination_column(client, app_context):
    admin, _member, board = setup_board()
    column = make_column(board)
    a, b = make_card(column, "A", 1024.0), make_card(column, "B", 2048.0)
    mover = make_card(make_column(board, "Other", 2048.0), "M", 1024.0)
    response = client.patch(
        f"/api/cards/{mover.id}/position", json={"column_id": str(column.id), "order": 2048.0}, headers=auth(admin)
    )
    data = response.get_json()["data"]
    assert response.status_code == 200 and data["rebalanced"] is True
    detail = client.get(f"/api/boards/{board.id}", headers=auth(admin)).get_json()["data"]
    cards = next(c for c in detail["columns"] if c["id"] == str(column.id))["cards"]
    assert [c["title"] for c in cards] == ["A", "M", "B"]
    assert [c["order"] for c in cards] == [1024.0, 2048.0, 3072.0]


def test_move_same_place_is_a_noop(client, app_context):
    admin, _member, board = setup_board()
    column = make_column(board)
    card = make_card(column)
    response = client.patch(
        f"/api/cards/{card.id}/position", json={"column_id": str(column.id), "order": 1024.0}, headers=auth(admin)
    )
    assert response.status_code == 200 and response.get_json()["data"]["rebalanced"] is False


def test_card_position_schema_rejects_bad_input(client, app_context):
    admin, _member, board = setup_board()
    column = make_column(board)
    other_board = make_board(admin, "Other")
    foreign = make_column(other_board)
    card = make_card(column)
    url = f"/api/cards/{card.id}/position"
    good = str(column.id)
    cases = [
        {"column_id": "not-a-uuid", "order": 1},
        {"column_id": good, "order": 0},
        {"column_id": good, "order": -3},
        {"column_id": good, "order": "2"},
        {"column_id": good, "order": True},
        {"column_id": good, "order": None},
        {"column_id": good},
        {"order": 1},
        {"column_id": good, "order": 1, "position": 1},
        {"column_id": good, "order": 1, "rebalanced": True},
        {"column_id": str(foreign.id), "order": 1},
        {"column_id": "00000000-0000-4000-8000-000000000042", "order": 1},
    ]
    for body in cases:
        assert client.patch(url, json=body, headers=auth(admin)).status_code == 400, body
    raw = client.patch(url, data='{"column_id": "%s", "order": Infinity}' % good, content_type="application/json", headers=auth(admin))
    assert raw.status_code == 400


def test_move_by_non_member_is_404(client, app_context):
    admin, _member, board = setup_board()
    column = make_column(board)
    card = make_card(column)
    stranger = make_user()
    response = client.patch(
        f"/api/cards/{card.id}/position", json={"column_id": str(column.id), "order": 5}, headers=auth(stranger)
    )
    assert response.status_code == 404


def test_my_tasks_lists_assigned_cards_grouped_data(client, app_context):
    admin, member, board = setup_board()
    other = make_board(admin, "A second board")
    mine = make_card(make_column(board), "Mine", assignee=member)
    make_card(make_column(other), "Also mine", assignee=member)
    make_card(make_column(board, "X", 2048.0), "Not mine", assignee=admin)
    response = client.get("/api/cards?assignee=me", headers=auth(member))
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert {c["board_name"] for c in data} == {"Sprint board", "A second board"}
    assert {c["title"] for c in data} == {"Mine", "Also mine"}
    assert all("board_id" in c for c in data)


def test_my_tasks_requires_assignee_me(client, app_context):
    member = make_user()
    assert client.get("/api/cards", headers=auth(member)).status_code == 400
    assert client.get("/api/cards?assignee=other", headers=auth(member)).status_code == 400
    assert client.get("/api/cards?assignee=me&x=1", headers=auth(member)).status_code == 400
    assert client.get("/api/cards?assignee=me", headers=auth(member)).get_json() == {"data": []}