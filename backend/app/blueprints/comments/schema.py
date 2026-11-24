from marshmallow import Schema, fields, validate


class CommentSchema(Schema):
    content = fields.Str(required=True, validate=validate.Length(min=1))
