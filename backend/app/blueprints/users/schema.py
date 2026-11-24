from marshmallow import Schema, fields


class ProfileSchema(Schema):
    name = fields.Str(required=False)
    email = fields.Email(required=False)
