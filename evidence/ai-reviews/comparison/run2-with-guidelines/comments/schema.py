from marshmallow import fields

from ...schemas_common import RequestSchema, ResponseSchema, StrictUUID, TrimmedString, UtcDateTime


class CommentAuthorSchema(ResponseSchema):
    id = StrictUUID()
    name = fields.String()


class CommentSchema(ResponseSchema):
    """Comment output. `author_user` is a transient attribute set by the service."""

    id = StrictUUID()
    card_id = StrictUUID()
    content = fields.String()
    author = fields.Nested(CommentAuthorSchema, attribute="author_user")
    created_at = UtcDateTime()
    updated_at = UtcDateTime()


class CommentContentSchema(RequestSchema):
    """Body of create and edit: only `content`, trimmed and non-empty (unknown keys return 400)."""

    content = TrimmedString(required=True)

