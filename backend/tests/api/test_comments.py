"""Comments Blueprint (COMMENT-001 to COMMENT-004): 201, 400, 401, 403 and 404 coverage."""
from sqlalchemy import select

from app.extensions import db
from app.models import ActivityEvent, Comment, Notification
from tests.factories import add_member, auth, make_board, make_card, make_column, make_user


def setup_card(assignee=None):
    admin, member = make_user("Ada Admin"), make_user("Mia Member")
    board = make_board(admin)
    add_member(board, member)
    card = make_card(make_column(board), "Plan", assignee=assignee)
    return admin, member, card


def test_create_comment_returns_201_with_author(client, app_context):
    admin, _member, card = setup_card()
    response = client.post(f"/api/cards/{card.id}/comments", json={"content": " Looks good "}, headers=auth(admin))
    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["content"] == "Looks good"
    assert data["author"] == {"id": str(admin.id), "name": "Ada Admin"}
    assert data["card_id"] == str(card.id)
    event = db.session.execute(select(ActivityEvent)).scalar_one()
    assert event.type == "comment_created" and str(event.comment_id) == data["id"]


def test_create_comment_missing_or_blank_content_is_400(client, app_context):
    admin, _member, card = setup_card()
    url = f"/api/cards/{card.id}/comments"
    assert client.post(url, json={}, headers=auth(admin)).status_code == 400
    assert client.post(url, json={"content": "   "}, headers=auth(admin)).status_code == 400
    assert client.post(url, json={"content": 5}, headers=auth(admin)).status_code == 400
    assert client.post(url, json={"content": "x", "author_id": "1"}, headers=auth(admin)).status_code == 400
    assert db.session.execute(select(Comment)).first() is None


def test_comment_endpoints_without_token_are_401(client, app_context):
    _admin, _member, card = setup_card()
    assert client.post(f"/api/cards/{card.id}/comments", json={"content": "x"}).status_code == 401
    assert client.get(f"/api/cards/{card.id}/comments").status_code == 401


def test_non_member_cannot_see_or_comment_404(client, app_context):
    _admin, _member, card = setup_card()
    stranger = make_user()
    assert client.post(f"/api/cards/{card.id}/comments", json={"content": "x"}, headers=auth(stranger)).status_code == 404
    assert client.get(f"/api/cards/{card.id}/comments", headers=auth(stranger)).status_code == 404


def test_list_comments_in_creation_order(client, app_context, fixed_clock):
    from datetime import timedelta

    admin, member, card = setup_card()
    client.post(f"/api/cards/{card.id}/comments", json={"content": "first"}, headers=auth(admin))
    fixed_clock["now"] += timedelta(minutes=1)
    client.post(f"/api/cards/{card.id}/comments", json={"content": "second"}, headers=auth(member))
    response = client.get(f"/api/cards/{card.id}/comments", headers=auth(admin))
    assert response.status_code == 200
    assert [c["content"] for c in response.get_json()["data"]] == ["first", "second"]


def test_owner_can_edit_and_delete(client, app_context):
    admin, _member, card = setup_card()
    created = client.post(f"/api/cards/{card.id}/comments", json={"content": "v1"}, headers=auth(admin)).get_json()["data"]
    edited = client.patch(f"/api/comments/{created['id']}", json={"content": "v2"}, headers=auth(admin))
    assert edited.status_code == 200 and edited.get_json()["data"]["content"] == "v2"
    deleted = client.delete(f"/api/comments/{created['id']}", headers=auth(admin))
    assert deleted.status_code == 200 and deleted.get_json() == {"data": {"id": created["id"]}}
    assert db.session.execute(select(Comment)).first() is None
    # The activity event survives the hard delete (DA-14).
    assert db.session.execute(select(ActivityEvent)).scalar_one().type == "comment_created"


def test_non_owner_edit_and_delete_is_403_even_for_admin(client, app_context):
    admin, member, card = setup_card()
    created = client.post(f"/api/cards/{card.id}/comments", json={"content": "mine"}, headers=auth(member)).get_json()["data"]
    assert client.patch(f"/api/comments/{created['id']}", json={"content": "hijack"}, headers=auth(admin)).status_code == 403
    assert client.delete(f"/api/comments/{created['id']}", headers=auth(admin)).status_code == 403
    # Ownership is checked before validation.
    assert client.patch(f"/api/comments/{created['id']}", json={}, headers=auth(admin)).status_code == 403
    assert db.session.get(Comment, __import__("uuid").UUID(created["id"])).content == "mine"


def test_edit_with_blank_content_is_400(client, app_context):
    admin, _member, card = setup_card()
    created = client.post(f"/api/cards/{card.id}/comments", json={"content": "v1"}, headers=auth(admin)).get_json()["data"]
    assert client.patch(f"/api/comments/{created['id']}", json={"content": " "}, headers=auth(admin)).status_code == 400


def test_comment_on_assigned_card_notifies_the_assignee_without_the_text(client, app_context):
    admin, member, card = setup_card(assignee=None)
    client.patch(f"/api/cards/{card.id}", json={"assignee_id": str(member.id)}, headers=auth(admin))
    db.session.execute(Notification.__table__.delete())
    db.session.commit()
    client.post(f"/api/cards/{card.id}/comments", json={"content": "secret words"}, headers=auth(admin))
    note = db.session.execute(select(Notification)).scalar_one()
    assert note.user_id == member.id and note.type == "comment_added"
    assert "secret words" not in note.message


def test_comment_by_the_assignee_does_not_notify(client, app_context):
    admin, member, card = setup_card()
    client.patch(f"/api/cards/{card.id}", json={"assignee_id": str(member.id)}, headers=auth(admin))
    db.session.execute(Notification.__table__.delete())
    db.session.commit()
    client.post(f"/api/cards/{card.id}/comments", json={"content": "own"}, headers=auth(member))
    assert db.session.execute(select(Notification)).first() is None


def test_comments_on_a_deleted_card_are_404(client, app_context):
    admin, _member, card = setup_card()
    client.delete(f"/api/cards/{card.id}", headers=auth(admin))
    assert client.get(f"/api/cards/{card.id}/comments", headers=auth(admin)).status_code == 404
