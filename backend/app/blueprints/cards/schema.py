from marshmallow import fields, validate

from ...schemas_common import OrderField, RequestSchema, ResponseSchema, StrictUUID, TrimmedString, UtcDateTime


class CardSchema(ResponseSchema):
    """Card: `position` is exposed as `order` and never as `position` (CARD-001-AC11)."""

    id = StrictUUID()
    column_id = StrictUUID()
    title = fields.String()
    order = fields.Float(attribute="position")
    assignee_id = StrictUUID(allow_none=True)
    completed_at = UtcDateTime()
    created_at = UtcDateTime()
    updated_at = UtcDateTime()


class MyTaskCardSchema(CardSchema):
    board_id = StrictUUID()
    board_name = fields.String()


class CreateCardSchema(RequestSchema):
    # `assignee_id` is not accepted at creation (CARD-002-AC08), so it is rejected as an unknown key.
    title = TrimmedString(required=True)


class UpdateCardSchema(RequestSchema):
    title = TrimmedString()
    assignee_id = StrictUUID(allow_none=True)


class CardPositionSchema(RequestSchema):
    """Validated move target: a UUID column_id and a positive float order (CARD-006)."""

    column_id = StrictUUID(required=True)
    order = OrderField(required=True)


class MyTasksQuerySchema(RequestSchema):
    """Only `assignee=me` is accepted. Any other value or parameter returns 400 (DA-19)."""

    assignee = fields.String(required=True, validate=validate.Equal("me"))