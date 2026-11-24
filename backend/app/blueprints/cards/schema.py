from marshmallow import Schema, fields, validate


class CardSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=1))
    assignee_id = fields.UUID(allow_none=True, load_default=None)


class CardPositionSchema(Schema):
    column_id = fields.UUID(required=True)
    order = fields.Float(required=True, validate=validate.Range(min=0.0000001))
