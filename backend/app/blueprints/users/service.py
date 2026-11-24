from app.auth import current_user_id
from app.extensions import db
from app.models import User


def get_profile():
    return db.session.get(User, current_user_id())


def update_profile(data):
    user = get_profile()
    if "name" in data:
        user.name = data["name"].strip()
    if "email" in data:
        user.email = data["email"].strip().lower()
    db.session.commit()
    return user
