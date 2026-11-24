"""Password hashing (DA-05). The method and its parameters are explicit and confined to this module."""
from werkzeug.security import check_password_hash, generate_password_hash

# Provisional development parameters (V-01 benchmark pending on the hosting plan).
HASH_METHOD = "scrypt:32768:8:1"

_dummy_hash: str | None = None


def hash_password(password: str) -> str:
    return generate_password_hash(password, method=HASH_METHOD)


def verify_password(password_hash: str, password: str) -> bool:
    return check_password_hash(password_hash, password)


def verify_dummy(password: str) -> None:
    """Spend the same time as a real check when the email is unknown (AUTH-002-AC03)."""
    global _dummy_hash
    if _dummy_hash is None:
        _dummy_hash = hash_password("revotask-dummy-password")
    check_password_hash(_dummy_hash, password)
