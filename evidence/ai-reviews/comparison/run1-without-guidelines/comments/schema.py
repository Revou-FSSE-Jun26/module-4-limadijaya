from marshmallow import fields

from ...schemas_common import RequestSchema, ResponseSchema, StrictUUID, TrimmedString, UtcDateTime


class CommentContentSchema(RequestSchema):
    content = TrimmedString(required=True)


class AuthorSchema(ResponseSchema):
    id = StrictUUID()
    name = fields.String()


class CommentSchema(ResponseSchema):
    id = StrictUUID()
    card_id = StrictUUID()
    content = fields.String()
    author = fields.Nested(AuthorSchema)
    created_at = UtcDateTime()
    updated_at = UtcDateTime()
