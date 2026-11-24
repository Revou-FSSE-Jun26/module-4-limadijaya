"""Notifications and analytics Blueprints (NOTIF-001, NOTIF-002, ANALYTICS-001 to ANALYTICS-006)."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.extensions import db
from app.models import Notification
from tests.factories import EPOCH, add_member, auth, make_board, make_card, make_column, make_user


def seed_notifications(count):
    admin, member = make_user("Ada Admin"), make_user("Mia Member")
    board = make_board(admin)
    add_member(board, member)
    card = make_card(make_column(board), "Plan")
    for index in range(count):
        db.session.add(
            Notification(
                user_id=member.id, actor_id=admin.id, board_id=board.id, card_id=card.id,
                type="card_assigned", message=f"n{index}", is_read=index % 2 == 0,
                created_at=EPOCH + timedelta(minutes=index),
            )
        )
    db.session.commit()
    return admin, member, board, card


def test_notifications_are_paginated_newest_first(client, app_context):
    _admin, member, _board, _card = seed_notifications(5)
    first = client.get("/api/notifications?page=1&per_page=2", headers=auth(member)).get_json()["data"]
    assert [n["message"] for n in first["items"]] == ["n4", "n3"]
    assert first["total"] == 5 and first["page"] == 1 and first["per_page"] == 2
    assert first["unread_count"] == 2  # indexes 1 and 3 are unread
    last = client.get("/api/notifications?page=3&per_page=2", headers=auth(member)).get_json()["data"]
    assert [n["message"] for n in last["items"]] == ["n0"]
    beyond = client.get("/api/notifications?page=9&per_page=2", headers=auth(member)).get_json()["data"]
    assert beyond["items"] == []


def test_notification_item_shape(client, app_context):
    _admin, member, _board, _card = seed_notifications(1)
    item = client.get("/api/notifications", headers=auth(member)).get_json()["data"]["items"][0]
    assert set(item) == {"id", "type", "message", "board_id", "card_id", "actor", "is_read", "created_at"}
    assert set(item["actor"]) == {"id", "name"}


def test_notification_query_validation(client, app_context):
    member = make_user()
    for query in ("page=0", "page=-1", "page=abc", "per_page=0", "per_page=1.5", "per_page=101", "x=1"):
        assert client.get(f"/api/notifications?{query}", headers=auth(member)).status_code == 400, query
    default = client.get("/api/notifications", headers=auth(member)).get_json()["data"]
    assert default["per_page"] == 20 and default["items"] == []


def test_only_my_notifications_are_listed(client, app_context):
    admin, _member, _board, _card = seed_notifications(2)
    assert client.get("/api/notifications", headers=auth(admin)).get_json()["data"]["total"] == 0


def test_mark_read_is_idempotent_and_recipient_only(client, app_context):
    admin, member, _board, _card = seed_notifications(2)
    unread = db.session.execute(select(Notification).where(Notification.is_read.is_(False))).scalar_one()
    url = f"/api/notifications/{unread.id}/read"
    assert client.patch(url, headers=auth(admin)).status_code == 404  # not the recipient
    first = client.patch(url, headers=auth(member))
    second = client.patch(url, headers=auth(member))
    assert first.status_code == second.status_code == 200
    assert first.get_json()["data"]["is_read"] is True
    missing = client.patch("/api/notifications/00000000-0000-4000-8000-000000000001/read", headers=auth(member))
    assert missing.status_code == 404 and missing.get_json() == client.patch(url, headers=auth(admin)).get_json()


def monday_noon():
    return datetime(2026, 11, 23, 12, 0, 0, tzinfo=timezone.utc)  # a Monday


def test_analytics_counts_per_column_completed_and_member_activity(client, app_context, fixed_clock):
    fixed_clock["now"] = monday_noon()
    admin, member = make_user("Ada Admin"), make_user("Zed Member")
    board = make_board(admin)
    add_member(board, member)
    todo = make_column(board, "To do", 1024.0)
    done = make_column(board, "Done", 2048.0, is_done=True)
    empty = make_column(board, "Empty", 3072.0)
    first = client.post(f"/api/columns/{todo.id}/cards", json={"title": "A"}, headers=auth(admin)).get_json()["data"]
    client.post(f"/api/columns/{todo.id}/cards", json={"title": "B"}, headers=auth(member))
    client.patch(f"/api/cards/{first['id']}/position", json={"column_id": str(done.id), "order": 1024}, headers=auth(admin))
    client.post(f"/api/cards/{first['id']}/comments", json={"content": "done!"}, headers=auth(admin))
    response = client.get(f"/api/boards/{board.id}/analytics", headers=auth(member))
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert set(data) == {"window", "cards_per_column", "completed_this_week", "member_activity"}
    assert data["window"] == {"start": "2026-11-23T00:00:00Z", "end": "2026-11-30T00:00:00Z"}
    counts = {c["name"]: c["card_count"] for c in data["cards_per_column"]}
    assert counts == {"To do": 1, "Done": 1, "Empty": 0}
    assert [c["name"] for c in data["cards_per_column"]] == ["To do", "Done", "Empty"]
    assert data["completed_this_week"] == 1
    activity = {m["name"]: m["activity_count"] for m in data["member_activity"]}
    assert activity == {"Ada Admin": 3, "Zed Member": 1}  # created + moved + comment, and one created
    assert data["member_activity"][0]["name"] == "Ada Admin"


def test_analytics_excludes_events_outside_the_week(client, app_context, fixed_clock):
    fixed_clock["now"] = monday_noon() - timedelta(days=1)  # Sunday of the previous week
    admin = make_user("Ada")
    board = make_board(admin)
    column = make_column(board)
    client.post(f"/api/columns/{column.id}/cards", json={"title": "Old"}, headers=auth(admin))
    fixed_clock["now"] = monday_noon()
    data = client.get(f"/api/boards/{board.id}/analytics", headers=auth(admin)).get_json()["data"]
    assert data["member_activity"] == [{"user_id": str(admin.id), "name": "Ada", "activity_count": 0}]
    assert data["cards_per_column"][0]["card_count"] == 1


def test_analytics_empty_board_and_access_rules(client, app_context):
    admin, stranger = make_user(), make_user()
    board = make_board(admin)
    data = client.get(f"/api/boards/{board.id}/analytics", headers=auth(admin)).get_json()["data"]
    assert data["cards_per_column"] == [] and data["completed_this_week"] == 0
    assert client.get(f"/api/boards/{board.id}/analytics", headers=auth(stranger)).status_code == 404
    assert client.get(f"/api/boards/{board.id}/analytics?x=1", headers=auth(admin)).status_code == 400
