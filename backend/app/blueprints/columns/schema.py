from marshmallow import Schema, fields


class ColumnSchema(Schema):
    name = fields.Str(required=True)
    is_done = fields.Bool(load_default=False)


class ReorderSchema(Schema):
    ids = fields.List(fields.UUID(), required=True)
