from marshmallow import fields

from ...schemas_common import EmailField, RequestSchema, ResponseSchema, StrictUUID, TrimmedString


class UserSchema(ResponseSchema):
    """UserPublic: id, name, email. The password hash is never serialized."""

    id = StrictUUID()
    name = fields.String()
    email = fields.String()


class MemberRefSchema(ResponseSchema):
    """MemberRef: exactly id and name (BOARD-003-AC09)."""

    id = StrictUUID()
    name = fields.String()


class UpdateProfileSchema(RequestSchema):
    # `password` is deliberately absent, so it is rejected as an unknown key (USER-002).
    name = TrimmedString()
    email = EmailField()