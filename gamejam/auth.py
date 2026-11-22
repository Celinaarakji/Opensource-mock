"""Token authentication and role checks.

Clients send `Authorization: Bearer <api_token>`. Tokens are created when a
user is created. There are no passwords in this project: it is a teaching
codebase, not something to deploy.
"""

import secrets

from gamejam import db
from gamejam.errors import Forbidden, Unauthorized


def generate_token():
    return secrets.token_hex(16)


def parse_bearer(header):
    """Return the token from an Authorization header, or None."""
    if not header:
        return None
    parts = header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1]


def user_from_header(conn, header):
    """Look up the user for an Authorization header, or None."""
    token = parse_bearer(header)
    if not token:
        return None
    return db.fetch_one(conn, "SELECT * FROM users WHERE api_token = ?", (token,))


def require_user(user):
    if user is None:
        raise Unauthorized("Send a valid 'Authorization: Bearer <token>' header")
    return user


def require_role(user, *roles):
    """Raise unless the user has one of the given roles."""
    require_user(user)
    if user["role"] not in roles:
        raise Forbidden(f"This action needs one of these roles: {', '.join(roles)}")
    return user


def public_user(user):
    """The fields of a user that are safe to show to other people."""
    if user is None:
        return None
    return {
        "id": user["id"],
        "username": user["username"],
        "display_name": user["display_name"],
        "role": user["role"],
    }
