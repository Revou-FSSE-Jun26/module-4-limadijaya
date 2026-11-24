from marshmallow import fields

from ...schemas_common import RequestSchema, ResponseSchema, StrictUUID, TrimmedString, UtcDateTime
from ..users.schema import MemberRefSchema


class CommentSchema(ResponseSchema):
    id = StrictUUID()
    card_id = StrictUUID()
    content = fields.String()
    author = fields.Nested(MemberRefSchema)
    created_at = UtcDateTime()
    updated_at = UtcDateTime()


class CommentContentSchema(RequestSchema):
    content = TrimmedString(required=True)