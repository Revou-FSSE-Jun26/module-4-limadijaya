from marshmallow import Schema, fields


class BoardSchema(Schema):
    name = fields.Str(required=True)


class MemberSchema(Schema):
    email = fields.Email(required=True)
