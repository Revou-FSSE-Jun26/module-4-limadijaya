import re

from marshmallow import ValidationError, fields

from ...schemas_common import RequestSchema, ResponseSchema, StrictUUID, UtcDateTime
from ..users.schema import MemberRefSchema

DEFAULT_PER_PAGE = 20  # UD-09 proposal, adopted by the delegated owner decision recorded in the CHANGELOG
MAX_PER_PAGE = 100


class PositiveIntQuery(fields.Field):
    """A query-string value that must be a positive integer."""

    def _deserialize(self, value, attr, data, **kwargs):
        if not isinstance(value, str) or not re.fullmatch(r"[0-9]{1,9}", value) or int(value) < 1:
            raise ValidationError("must be a positive integer")
        return int(value)


class NotificationQuerySchema(RequestSchema):
    page = PositiveIntQuery(load_default=1)
    per_page = PositiveIntQuery(load_default=DEFAULT_PER_PAGE)


class NotificationSchema(ResponseSchema):
    id = StrictUUID()
    type = fields.String()
    message = fields.String()
    board_id = StrictUUID()
    card_id = StrictUUID()
    actor = fields.Nested(MemberRefSchema)
    is_read = fields.Boolean()
    created_at = UtcDateTime()