from sqlalchemy import func, select

from ...access import get_live_card_or_404, get_live_column_or_404, get_membership, require_member
from ...activity import EVENT_CARD_CREATED, EVENT_CARD_MOVED, notify, record_event
from ...clock import utcnow
from ...errors import BadRequestError, NotFoundError
from ...extensions import db
from ...locking import lock_card, lock_column
from ...models import Board, BoardColumn, Card, User
from ...models.notification import TYPE_CARD_ASSIGNED
from ...queries import live_cards
from ...schemas_common import load_query, require_object
from .schema import CardPositionSchema, CreateCardSchema, MyTasksQuerySchema, UpdateCardSchema

SPACING = 1024.0  # A-01 and the tie rebalance spacing (design 8.2)
INVALID_ASSIGNEE = "Invalid assignee."
INVALID_COLUMN = "Invalid column."


def create_card(user_id, column_id, raw) -> Card:
    column = get_live_column_or_404(column_id)
    require_member(user_id, column.board_id)
    data = CreateCardSchema().load(require_object(raw))
    now = utcnow()
    column = lock_column(column_id)
    if column is None or column.deleted_at is not None:
        raise NotFoundError()
    top = db.session.execute(
        select(func.max(Card.position)).where(Card.column_id == column_id, Card.deleted_at.is_(None))
    ).scalar()
    card = Card(
        column_id=column_id,
        title=data["title"],
        position=SPACING if top is None else top + SPACING,
        completed_at=now if column.is_done else None,
        created_at=now,
        updated_at=now,
    )
    db.session.add(card)
    db.session.flush()
    record_event(column.board_id, user_id, EVENT_CARD_CREATED, card.id, now)
    db.session.commit()
    return card


def update_card(user_id, card_id, raw) -> Card:
    card, column = get_live_card_or_404(card_id)
    require_member(user_id, column.board_id)
    data = UpdateCardSchema().load(require_object(raw))
    if not data:
        raise BadRequestError("Invalid request: provide title or assignee_id.")
    now = utcnow()
    card = lock_card(card_id)
    if card is None or card.deleted_at is not None:
        raise NotFoundError()

    changed = False
    if "title" in data and card.title != data["title"]:
        card.title = data["title"]
        changed = True

    notify_assignee = None
    if "assignee_id" in data and data["assignee_id"] != card.assignee_id:
        new_assignee = data["assignee_id"]
        if new_assignee is not None:
            if db.session.get(User, new_assignee) is None or get_membership(new_assignee, column.board_id) is None:
                raise BadRequestError(INVALID_ASSIGNEE)
            if new_assignee != user_id:
                notify_assignee = new_assignee
        card.assignee_id = new_assignee
        changed = True

    if changed:
        card.updated_at = now
        if notify_assignee is not None:
            actor = db.session.get(User, user_id)
            notify(
                notify_assignee,
                actor,
                column.board_id,
                card,
                TYPE_CARD_ASSIGNED,
                f'{actor.name} assigned you to "{card.title}"',
                now,
            )
        db.session.commit()
    return card


def delete_card(user_id, card_id) -> dict:
    card, column = get_live_card_or_404(card_id)
    require_member(user_id, column.board_id)
    card = lock_card(card_id)
    if card is None or card.deleted_at is not None:
        raise NotFoundError()
    card.deleted_at = utcnow()
    db.session.commit()
    return {"id": str(card_id)}


def move_card(user_id, card_id, raw) -> tuple[Card, bool]:
    card, source_column = get_live_card_or_404(card_id)
    require_member(user_id, source_column.board_id)
    data = CardPositionSchema().load(require_object(raw))
    board_id = source_column.board_id

    destination = db.session.get(BoardColumn, data["column_id"])
    if destination is None or destination.board_id != board_id or destination.deleted_at is not None:
        raise BadRequestError(INVALID_COLUMN)

    now = utcnow()
    destination = lock_column(destination.id)
    if destination is None or destination.deleted_at is not None:
        raise BadRequestError(INVALID_COLUMN)
    card = lock_card(card_id)
    if card is None or card.deleted_at is not None:
        raise NotFoundError()

    same_column = card.column_id == destination.id
    order = data["order"]
    if same_column and card.position == order:
        return card, False  # no-op: no write, no event

    others = list(
        db.session.execute(
            live_cards(destination.id)
            .where(Card.id != card.id)
            .order_by(Card.position, Card.created_at, Card.id)
            .execution_options(populate_existing=True)
        ).scalars()
    )
    tie = next((other for other in others if other.position == order), None)
    rebalanced = False
    if tie is not None:
        sequence = []
        for other in others:
            if other is tie:
                sequence.append(card)
            sequence.append(other)
        for index, member in enumerate(sequence):
            value = SPACING * (index + 1)
            if member.position != value:
                member.position = value
                if member is not card:
                    member.updated_at = now
        rebalanced = True
    else:
        card.position = order

    completed_at = (card.completed_at or now) if destination.is_done else None
    card.completed_at = completed_at
    if not same_column:
        card.column_id = destination.id
        record_event(
            board_id, user_id, EVENT_CARD_MOVED, card.id, now, from_column_id=source_column.id, to_column_id=destination.id
        )
    card.updated_at = now
    db.session.commit()
    return card, rebalanced


def list_my_tasks(user_id, args) -> list[dict]:
    load_query(MyTasksQuerySchema(), args)
    rows = db.session.execute(
        select(Card, Board.id, Board.name)
        .join(BoardColumn, BoardColumn.id == Card.column_id)
        .join(Board, Board.id == BoardColumn.board_id)
        .where(Card.assignee_id == user_id, Card.deleted_at.is_(None), BoardColumn.deleted_at.is_(None))
        .order_by(Board.name, Board.id, BoardColumn.position, Card.position, Card.id)
    ).all()
    result = []
    for card, board_id, board_name in rows:
        card.board_id = board_id  # transient attributes read by MyTaskCardSchema
        card.board_name = board_name
        result.append(card)
    return result