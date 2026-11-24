"""Shared Marshmallow primitives (BE-06). Every request schema rejects unknown keys."""
from __future__ import annotations

import math
import re
import uuid
from datetime import datetime, timezone

from marshmallow import EXCLUDE, RAISE, Schema, ValidationError, fields

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def iso(value: datetime | None) -> str | None:
    """ISO 8601 UTC string with an explicit Z."""
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class RequestSchema(Schema):
    """Base for request bodies: unknown keys return 400."""

    class Meta:
        unknown = RAISE


class ResponseSchema(Schema):
    """Base for response dumps."""

    class Meta:
        unknown = EXCLUDE


class UtcDateTime(fields.Field):
    def _serialize(self, value, attr, obj, **kwargs):
        return iso(value)


class TrimmedString(fields.String):
    """A real string, trimmed, and non-empty after trimming."""

    def _deserialize(self, value, attr, data, **kwargs):
        text = super()._deserialize(value, attr, data, **kwargs).strip()
        if not text:
            raise ValidationError("must not be empty")
        return text


class EmailField(TrimmedString):
    """Trimmed, lowercased, syntactically valid email (DA-06)."""

    def _deserialize(self, value, attr, data, **kwargs):
        text = super()._deserialize(value, attr, data, **kwargs).lower()
        if not EMAIL_PATTERN.match(text):
            raise ValidationError("must be a valid email address")
        return text


class StrictUUID(fields.Field):
    """Accepts only a UUID string."""

    def _deserialize(self, value, attr, data, **kwargs):
        if not isinstance(value, str):
            raise ValidationError("must be a UUID string")
        try:
            return uuid.UUID(value)
        except ValueError:
            raise ValidationError("must be a UUID string") from None

    def _serialize(self, value, attr, obj, **kwargs):
        return None if value is None else str(value)


class StrictNumber(fields.Field):
    """A positive, finite JSON number. Rejects bool, str, None, NaN, Infinity, 0, negatives."""

    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValidationError("must be a number")
        try:
            number = float(value)
        except OverflowError:
            raise ValidationError("must be a finite number") from None
        if not math.isfinite(number):
            raise ValidationError("must be a finite number")
        if number <= 0:
            raise ValidationError("must be greater than zero")
        return number


class OrderField(StrictNumber):
    """Public name `order`, stored as `position` (DB-05)."""


def load_query(schema: Schema, args) -> dict:
    """Validate a query string. Repeated keys are rejected."""
    flat: dict[str, str] = {}
    for key in args.keys():
        values = args.getlist(key)
        if len(values) != 1:
            raise ValidationError({key: ["must appear once"]})
        flat[key] = values[0]
    return schema.load(flat)


def require_object(raw) -> dict:
    if not isinstance(raw, dict):
        raise ValidationError({"_schema": ["body must be a JSON object"]})
    return raw


class StrictBool(fields.Field):
    """Only JSON true or false. Strings and numbers are rejected."""

    def _deserialize(self, value, attr, data, **kwargs):
        if not isinstance(value, bool):
            raise ValidationError("must be true or false")
        return value
