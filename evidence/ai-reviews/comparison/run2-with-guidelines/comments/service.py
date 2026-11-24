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


def create_comment(user_id, card_id, raw) -> Comment:
    card, column = get_live_card_or_404(card_id)  # 404: missing or soft-deleted card or column
    board_id = column.board_id
    require_member(user_id, board_id)  # 404 for a non-member
    data = CommentContentSchema().load(require_object(raw))  # 400 only after the checks above
    now = utcnow()
    card = lock_card(card_id, share=True)  # FOR SHARE: assignee and deleted_at cannot change (BE-17)
    if card is None or card.deleted_at is not None:
        raise NotFoundError()
    author = db.session.get(User, user_id)
    comment = Comment(card_id=card.id, author_id=user_id, content=data["content"], created_at=now, updated_at=now)
    db.session.add(comment)
    db.session.flush()
    record_event(board_id, user_id, EVENT_COMMENT_CREATED, card.id, now, comment_id=comment.id)
    if card.assignee_id is not None and card.assignee_id != user_id:
        # The message never contains the comment text.
        notify(
            card.assignee_id,
            author,
            board_id,
            card,
            TYPE_COMMENT_ADDED,
            f'{author.name} commented on "{card.title}"',
            now,
        )
    db.session.commit()
    comment.author_user = author
    return comment


def list_comments(user_id, card_id) -> list[Comment]:
    _card, column = get_live_card_or_404(card_id)
    require_member(user_id, column.board_id)
    rows = db.session.execute(
        select(Comment, User)
        .join(User, User.id == Comment.author_id)
        .where(Comment.card_id == card_id)
        .order_by(Comment.created_at, Comment.id)
    ).all()
    comments = []
    for comment, author in rows:
        comment.author_user = author  # transient attribute read by CommentSchema
        comments.append(comment)
    return comments


def update_comment(user_id, comment_id, raw) -> Comment:
    comment, _card, column = get_comment_or_404(comment_id)
    require_member(user_id, column.board_id)  # 404 for a non-member
    require_comment_owner(user_id, comment)  # 403 for any non-owner, administrators included
    data = CommentContentSchema().load(require_object(raw))  # 400 only now
    if comment.content != data["content"]:
        comment.content = data["content"]
        comment.updated_at = utcnow()
        db.session.commit()
    comment.author_user = db.session.get(User, comment.author_id)
    return comment


def delete_comment(user_id, comment_id) -> dict:
    comment, _card, column = get_comment_or_404(comment_id)
    require_member(user_id, column.board_id)
    require_comment_owner(user_id, comment)
    db.session.delete(comment)  # hard delete (DB-06); the activity event keeps its plain comment_id
    db.session.commit()
    return {"id": str(comment_id)}

