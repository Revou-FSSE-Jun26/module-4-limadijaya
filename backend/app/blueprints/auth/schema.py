from marshmallow import fields, validate

from ...schemas_common import EmailField, RequestSchema, TrimmedString


class RegisterSchema(RequestSchema):
    name = TrimmedString(required=True)
    email = EmailField(required=True)
    # Passwords are never trimmed or echoed. The only rule is "present and non-empty" (UD-21 is open).
    password = fields.String(required=True, validate=validate.Length(min=1))


class LoginSchema(RequestSchema):
    email = TrimmedString(required=True)
    password = fields.String(required=True, validate=validate.Length(min=1))