from flask_jwt_extended import create_access_token
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from app.errors import ConflictError
from app.clock import utc_now
from app.extensions import db
from app.models import User


def register(data):
    email = data["email"].strip().lower()
    now = utc_now()
    user = User(name=data.get("name", email.split("@")[0]).strip(), email=email, password_hash=generate_password_hash(data["password"]), created_at=now, updated_at=now)
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ConflictError("Email is already registered.") from None
    return user


def login(data):
    user = User.query.filter_by(email=data["email"].strip().lower()).first()
    if user is None or not check_password_hash(user.password_hash, data["password"]):
        raise ConflictError("Invalid email or password.")
    return user, create_access_token(identity=str(user.id))
