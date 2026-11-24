from marshmallow import Schema, ValidationError, fields, validates


class CommentInputSchema(Schema):
    content = fields.String(required=True, allow_none=False)

    @validates("content")
    def _not_blank(self, value, **kwargs):
        if not value.strip():
            raise ValidationError("content must not be empty")


class AuthorSchema(Schema):
    id = fields.String()
    name = fields.String()


class CommentOutputSchema(Schema):
    id = fields.String()
    card_id = fields.String()
    content = fields.String()
    author = fields.Nested(AuthorSchema)
    created_at = fields.String()
    updated_at = fields.String()


comment_input_schema = CommentInputSchema()
