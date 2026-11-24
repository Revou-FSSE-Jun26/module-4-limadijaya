from marshmallow import RAISE, Schema, ValidationError, fields, post_load


class CommentInputSchema(Schema):
    """Body of POST /cards/<id>/comments and PATCH /comments/<id>."""

    class Meta:
        unknown = RAISE

    content = fields.String(required=True)

    @post_load
    def trim_content(self, data, **kwargs):
        content = data["content"].strip()
        if not content:
            raise ValidationError("Content must not be empty.", field_name="content")
        data["content"] = content
        return data


class AuthorSchema(Schema):
    id = fields.UUID()
    name = fields.String()


class CommentSchema(Schema):
    """Output only. Dumps the dict built by the service (comment fields plus author)."""

    id = fields.UUID()
    card_id = fields.UUID()
    content = fields.String()
    author = fields.Nested(AuthorSchema)
    created_at = fields.DateTime(format="iso")
    updated_at = fields.DateTime(format="iso")
