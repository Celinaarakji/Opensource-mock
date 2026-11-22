"""Users: organizers, judges and participants."""

from gamejam import auth, db
from gamejam.errors import Conflict, NotFound
from gamejam.utils.time import now_iso
from gamejam.validation import validate_user


def create_user(conn, body, token=None):
    """Create a user from a request body. Returns the full row, token included."""
    data = validate_user(body)
    if db.fetch_one(conn, "SELECT id FROM users WHERE username = ?", (data["username"],)):
        raise Conflict("That username is taken")
    if db.fetch_one(conn, "SELECT id FROM users WHERE email = ?", (data["email"],)):
        raise Conflict("That email is already registered")
    data["api_token"] = token or auth.generate_token()
    data["created_at"] = now_iso()
    user_id = db.insert(conn, "users", data)
    return get_user(conn, user_id)


def get_user(conn, user_id):
    user = db.fetch_one(conn, "SELECT * FROM users WHERE id = ?", (user_id,))
    if user is None:
        raise NotFound(f"User {user_id} not found")
    return user


def get_user_by_username(conn, username):
    return db.fetch_one(conn, "SELECT * FROM users WHERE username = ?", (username,))


def list_users(conn, role=None):
    if role:
        return db.fetch_all(conn, "SELECT * FROM users WHERE role = ? ORDER BY id", (role,))
    return db.fetch_all(conn, "SELECT * FROM users ORDER BY id")


def user_jams(conn, user_id):
    """Every jam the user is part of, as a member of a team."""
    return db.fetch_all(
        conn,
        """
        SELECT j.id, j.name, j.slug, t.id AS team_id, t.name AS team_name
        FROM team_members m
        JOIN teams t ON t.id = m.team_id
        JOIN jams j ON j.id = t.jam_id
        WHERE m.user_id = ?
        ORDER BY j.starts_at DESC
        """,
        (user_id,),
    )
