from sqlalchemy import select

from ...access import get_comment_or_404, get_live_card_or_404, require_comment_owner, require_member
from ...activity import EVENT_COMMENT_CREATED, notify, record_event
from ...clock import utcnow
from ...errors import NotFoundError
from ...extensions import db
from ...locking import lock_card
from ...models import Comment, User
from ...models.notification import TYPE_COMMENT_ADDED
from ...schemas_common import require_object
from .schema import CommentContentSchema


def _view(comment: Comment, author: User) -> dict:
    return {
        "id": comment.id,
        "card_id": comment.card_id,
        "content": comment.content,
        "author": {"id": author.id, "name": author.name},
        "created_at": comment.created_at,
        "updated_at": comment.updated_at,
    }


def create_comment(user_id, card_id, raw) -> dict:
    card, column = get_live_card_or_404(card_id)
    require_member(user_id, column.board_id)
    data = CommentContentSchema().load(require_object(raw))
    now = utcnow()
    card = lock_card(card_id, share=True)
    if card is None or card.deleted_at is not None:
        raise NotFoundError()
    author = db.session.get(User, user_id)
    comment = Comment(
        card_id=card.id,
        author_id=user_id,
        content=data["content"],
        created_at=now,
        updated_at=now,
    )
    db.session.add(comment)
    db.session.flush()
    record_event(column.board_id, user_id, EVENT_COMMENT_CREATED, card.id, now, comment_id=comment.id)
    if card.assignee_id is not None and card.assignee_id != user_id:
        notify(
            card.assignee_id,
            author,
            column.board_id,
            card,
            TYPE_COMMENT_ADDED,
            f'{author.name} commented on "{card.title}"',
            now,
        )
    db.session.commit()
    return _view(comment, author)


def list_comments(user_id, card_id) -> list[dict]:
    _card, column = get_live_card_or_404(card_id)
    require_member(user_id, column.board_id)
    rows = db.session.execute(
        select(Comment, User)
        .join(User, User.id == Comment.author_id)
        .where(Comment.card_id == card_id)
        .order_by(Comment.created_at.asc(), Comment.id.asc())
    ).all()
    return [_view(comment, author) for comment, author in rows]


def update_comment(user_id, comment_id, raw) -> dict:
    comment, _card, column = get_comment_or_404(comment_id)
    require_member(user_id, column.board_id)
    require_comment_owner(user_id, comment)
    data = CommentContentSchema().load(require_object(raw))
    comment.content = data["content"]
    comment.updated_at = utcnow()
    author = db.session.get(User, comment.author_id)
    db.session.commit()
    return _view(comment, author)


def delete_comment(user_id, comment_id) -> dict:
    comment, _card, column = get_comment_or_404(comment_id)
    require_member(user_id, column.board_id)
    require_comment_owner(user_id, comment)
    deleted_id = comment.id
    db.session.delete(comment)
    db.session.commit()
    return {"id": str(deleted_id)}
