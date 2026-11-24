from marshmallow import ValidationError, fields, validate, validates_schema

from ...schemas_common import (
    OrderField,
    RequestSchema,
    ResponseSchema,
    StrictBool,
    StrictUUID,
    TrimmedString,
)


class ColumnSchema(ResponseSchema):
    """Column: id, name, order, is_done. `position` and `deleted_at` are never exposed."""

    id = StrictUUID()
    name = fields.String()
    order = fields.Float(attribute="position")
    is_done = fields.Boolean()


class CreateColumnSchema(RequestSchema):
    name = TrimmedString(required=True)


class UpdateColumnSchema(RequestSchema):
    name = TrimmedString()
    is_done = StrictBool()


class ReorderEntrySchema(RequestSchema):
    id = StrictUUID(required=True)
    order = OrderField(required=True)


class ReorderSchema(RequestSchema):
    columns = fields.List(fields.Nested(ReorderEntrySchema), required=True, validate=validate.Length(min=1))

    @validates_schema
    def no_duplicates(self, data, **kwargs):
        entries = data.get("columns", [])
        if len({e["id"] for e in entries}) != len(entries):
            raise ValidationError("column ids must be unique", "columns")
        if len({e["order"] for e in entries}) != len(entries):
            raise ValidationError("order values must be unique", "columns")