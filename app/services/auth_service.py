"""
Authentication Service.

Handles password hashing, verification, and user authentication
using Werkzeug's security utilities.
"""

from werkzeug.security import generate_password_hash, check_password_hash
from app.database.queries import get_user_by_username, create_user


def hash_password(plain_password):
    """Hash a plain-text password using pbkdf2:sha256."""
    return generate_password_hash(plain_password, method='pbkdf2:sha256')


def verify_password(stored_hash, plain_password):
    """Verify a plain-text password against a stored hash."""
    return check_password_hash(stored_hash, plain_password)


def authenticate_user(username, password):
    """
    Authenticate a user by username and password.
    Returns the user dict on success, None on failure.
    """
    user = get_user_by_username(username)

    if user is None:
        return None

    if not user.get('is_active', False):
        return None

    if not verify_password(user['password_hash'], password):
        return None

    return user


def register_user(username, email, plain_password, role):
    """
    Register a new user account.
    Returns the new user_id on success.
    Raises exception on duplicate username/email.
    """
    password_hash = hash_password(plain_password)
    return create_user(username, email, password_hash, role)
