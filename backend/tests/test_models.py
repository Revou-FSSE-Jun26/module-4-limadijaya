"""Metadata-level acceptance tests for the T2.02–T2.07 models."""

from app.models import (
    ActivityEvent,
    Board,
    BoardColumn,
    BoardMembership,
    Card,
    Comment,
    Notification,
    User,
)


def test_exact_application_tables_are_declared():
    assert {
        User.__tablename__,
        Board.__tablename__,
        BoardMembership.__tablename__,
        BoardColumn.__tablename__,
        Card.__tablename__,
        Comment.__tablename__,
        Notification.__tablename__,
        ActivityEvent.__tablename__,
    } == {
        "users",
        "boards",
        "board_memberships",
        "columns",
        "cards",
        "comments",
        "notifications",
        "activity_events",
    }


def test_membership_has_role_check_and_unique_board_user_constraint():
    constraints = BoardMembership.__table__.constraints
    assert any(
        constraint.name == "ck_board_memberships_role"
        and "administrator" in str(constraint.sqltext)
        and "member" in str(constraint.sqltext)
        for constraint in constraints
    )
    assert any(
        constraint.name == "uq_board_memberships_board_user"
        for constraint in constraints
    )


def test_ordering_and_soft_delete_columns_match_the_design():
    assert isinstance(BoardColumn.__table__.c.position.type.python_type, type)
    assert BoardColumn.__table__.c.position.nullable is False
    assert Card.__table__.c.position.nullable is False
    assert BoardColumn.__table__.c.is_done.nullable is False
    assert BoardColumn.__table__.c.deleted_at.nullable is True
    assert Card.__table__.c.deleted_at.nullable is True
    assert Card.__table__.c.completed_at.nullable is True


def test_notification_and_activity_event_checks_are_restricted():
    notification_checks = {c.name: str(c.sqltext) for c in Notification.__table__.constraints if c.name}
    activity_checks = {c.name: str(c.sqltext) for c in ActivityEvent.__table__.constraints if c.name}
    assert "card_assigned" in notification_checks["ck_notifications_type"]
    assert "comment_added" in notification_checks["ck_notifications_type"]
    assert "card_created" in activity_checks["ck_activity_events_type"]
    assert "card_moved" in activity_checks["ck_activity_events_type"]
    assert "comment_created" in activity_checks["ck_activity_events_type"]
    assert "from_column_id IS NOT NULL" in activity_checks["ck_activity_events_move_columns"]


def test_board_owned_foreign_keys_use_database_cascade():
    for model, column in (
        (BoardMembership, "board_id"),
        (BoardColumn, "board_id"),
        (Card, "column_id"),
        (Comment, "card_id"),
        (Notification, "board_id"),
        (ActivityEvent, "board_id"),
    ):
        foreign_key = next(iter(getattr(model.__table__.c, column).foreign_keys))
        assert foreign_key.ondelete == "CASCADE"
