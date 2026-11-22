"""Shared test helpers.

`make_conn()` gives you a fresh in-memory database with the demo data, and
`ApiClient` sends requests through the router without starting a server.
"""

import json

from gamejam import db
from gamejam.app import create_router
from gamejam.seed import seed, token_for
from gamejam.services import users
from gamejam.web import dispatch


def make_conn(with_demo_data=True):
    conn = db.get_connection(":memory:")
    if with_demo_data:
        seed(conn)
    else:
        db.init_db(conn)
    return conn


def user(conn, username):
    """Fetch a demo user by username."""
    return users.get_user_by_username(conn, username)


def jam_id(conn, slug):
    return conn.execute("SELECT id FROM jams WHERE slug = ?", (slug,)).fetchone()[0]


def team_id(conn, name):
    return conn.execute("SELECT id FROM teams WHERE name = ?", (name,)).fetchone()[0]


WINTER = "winter-game-jam-2026"
SPRING = "spring-mini-jam-2027"
SUMMER = "summer-jam-2027"


class ApiClient:
    def __init__(self, conn):
        self.conn = conn
        self.router = create_router()

    def request(self, method, path, as_user=None, body=None):
        headers = {}
        if as_user:
            headers["Authorization"] = f"Bearer {token_for(as_user)}"
        raw = json.dumps(body).encode("utf-8") if body is not None else b""
        response = dispatch(self.router, self.conn, method, path, headers, raw)
        return response.status, response.body

    def get(self, path, as_user=None):
        return self.request("GET", path, as_user)

    def post(self, path, body=None, as_user=None):
        return self.request("POST", path, as_user, body or {})

    def patch(self, path, body=None, as_user=None):
        return self.request("PATCH", path, as_user, body or {})

    def delete(self, path, as_user=None):
        return self.request("DELETE", path, as_user)
