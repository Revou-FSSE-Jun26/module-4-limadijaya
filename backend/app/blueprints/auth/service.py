from flask_jwt_extended import create_access_token
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ...clock import utcnow
from ...errors import AuthenticationError, ConflictError
from ...extensions import db
from ...models import User
from ...schemas_common import require_object
from ...security import hash_password, verify_dummy, verify_password
from .schema import LoginSchema, RegisterSchema

EMAIL_TAKEN = "An account with this email already exists."


def register(raw) -> User:
    data = RegisterSchema().load(require_object(raw))
    exists = db.session.execute(select(User.id).where(User.email == data["email"])).first()
    if exists:
        raise ConflictError(EMAIL_TAKEN)
    now = utcnow()
    user = User(
        name=data["name"],
        email=data["email"],
        password_hash=hash_password(data["password"]),
        created_at=now,
        updated_at=now,
    )
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ConflictError(EMAIL_TAKEN) from None
    return user


def login(raw) -> str:
    data = LoginSchema().load(require_object(raw))
    email = data["email"].lower()
    user = db.session.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is None:
        verify_dummy(data["password"])
        raise AuthenticationError()
    if not verify_password(user.password_hash, data["password"]):
        raise AuthenticationError()
    return create_access_token(identity=str(user.id))