from marshmallow import Schema, fields, validate


class CredentialsSchema(Schema):
    name = fields.Str(required=False, validate=validate.Length(min=1))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8))
