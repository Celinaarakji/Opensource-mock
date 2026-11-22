"""Database helpers.

Everything talks to SQLite through `get_connection()`. Rows come back as
`sqlite3.Row`, so you can use `row["name"]` or convert with `row_to_dict`.
"""

import sqlite3
from pathlib import Path

from gamejam import config

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def get_connection(path=None):
    """Open a connection with foreign keys on and dict-like rows."""
    conn = sqlite3.connect(path or config.DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn):
    """Create all tables if they don't exist yet."""
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.commit()


def row_to_dict(row):
    """Convert a sqlite3.Row (or None) into a plain dict (or None)."""
    if row is None:
        return None
    return {key: row[key] for key in row.keys()}


def rows_to_dicts(rows):
    return [row_to_dict(r) for r in rows]


def fetch_one(conn, sql, params=()):
    return row_to_dict(conn.execute(sql, params).fetchone())


def fetch_all(conn, sql, params=()):
    return rows_to_dicts(conn.execute(sql, params).fetchall())


def insert(conn, table, values):
    """Insert a dict of column -> value and return the new row id."""
    columns = ", ".join(values.keys())
    placeholders = ", ".join("?" for _ in values)
    cur = conn.execute(
        f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
        tuple(values.values()),
    )
    conn.commit()
    return cur.lastrowid


def update(conn, table, row_id, values):
    """Update columns on one row by id. Returns the number of rows changed."""
    if not values:
        return 0
    assignments = ", ".join(f"{col} = ?" for col in values)
    cur = conn.execute(
        f"UPDATE {table} SET {assignments} WHERE id = ?",
        (*values.values(), row_id),
    )
    conn.commit()
    return cur.rowcount


def delete(conn, table, row_id):
    cur = conn.execute(f"DELETE FROM {table} WHERE id = ?", (row_id,))
    conn.commit()
    return cur.rowcount
