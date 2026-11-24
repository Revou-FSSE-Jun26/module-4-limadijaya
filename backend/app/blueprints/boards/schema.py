from marshmallow import fields

from ...schemas_common import EmailField, RequestSchema, ResponseSchema, StrictUUID, TrimmedString, UtcDateTime


class BoardSummarySchema(ResponseSchema):
    id = StrictUUID()
    name = fields.String()
    created_at = UtcDateTime()
    updated_at = UtcDateTime()


class BoardNameSchema(RequestSchema):
    name = TrimmedString(required=True)


class AddMemberSchema(RequestSchema):
    email = EmailField(required=True)