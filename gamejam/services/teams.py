"""Teams and team membership."""

from gamejam import db
from gamejam.errors import BadRequest, Conflict, Forbidden, NotFound
from gamejam.services import jams
from gamejam.utils.time import now_iso
from gamejam.validation import validate_team


def create_team(conn, jam_id, body, captain):
    """Create a team in a jam. The person creating it becomes captain."""
    jam = jams.get_jam(conn, jam_id)
    jams.require_status(jam, "draft", "open")
    data = validate_team(body)
    existing = db.fetch_one(
        conn, "SELECT id FROM teams WHERE jam_id = ? AND name = ?", (jam_id, data["name"])
    )
    if existing:
        raise Conflict("A team with that name already exists in this jam")
    if user_team_in_jam(conn, jam_id, captain["id"]):
        raise Conflict("You are already on a team in this jam")
    now = now_iso()
    team_id = db.insert(
        conn,
        "teams",
        {"jam_id": jam_id, "name": data["name"], "captain_id": captain["id"], "created_at": now},
    )
    conn.execute(
        "INSERT INTO team_members (team_id, user_id, joined_at) VALUES (?, ?, ?)",
        (team_id, captain["id"], now),
    )
    conn.commit()
    return get_team_or_404(conn, team_id)


def get_team(conn, team_id):
    """The team row, or None if it doesn't exist."""
    return db.fetch_one(conn, "SELECT * FROM teams WHERE id = ?", (team_id,))


def get_team_or_404(conn, team_id):
    team = get_team(conn, team_id)
    if team is None:
        raise NotFound(f"Team {team_id} not found")
    return team


def list_teams(conn, jam_id):
    jams.get_jam(conn, jam_id)
    return db.fetch_all(
        conn,
        """
        SELECT t.*, COUNT(m.user_id) AS member_count
        FROM teams t LEFT JOIN team_members m ON m.team_id = t.id
        WHERE t.jam_id = ?
        GROUP BY t.id
        ORDER BY t.name
        """,
        (jam_id,),
    )


def list_members(conn, team_id):
    return db.fetch_all(
        conn,
        """
        SELECT u.id, u.username, u.display_name, m.joined_at
        FROM team_members m JOIN users u ON u.id = m.user_id
        WHERE m.team_id = ? ORDER BY m.joined_at
        """,
        (team_id,),
    )


def member_count(conn, team_id):
    return conn.execute(
        "SELECT COUNT(*) FROM team_members WHERE team_id = ?", (team_id,)
    ).fetchone()[0]


def is_member(conn, team_id, user_id):
    row = db.fetch_one(
        conn,
        "SELECT 1 AS ok FROM team_members WHERE team_id = ? AND user_id = ?",
        (team_id, user_id),
    )
    return row is not None


def user_team_in_jam(conn, jam_id, user_id):
    """The team a user is on in a jam, or None."""
    return db.fetch_one(
        conn,
        """
        SELECT t.* FROM teams t JOIN team_members m ON m.team_id = t.id
        WHERE t.jam_id = ? AND m.user_id = ?
        """,
        (jam_id, user_id),
    )


def add_member(conn, team_id, user, added_by):
    """Add a user to a team. Only the captain can add people."""
    team = get_team_or_404(conn, team_id)
    jam = jams.get_jam(conn, team["jam_id"])
    jams.require_status(jam, "draft", "open")
    if added_by["id"] != team["captain_id"]:
        raise Forbidden("Only the team captain can add members")
    if user_team_in_jam(conn, team["jam_id"], user["id"]):
        raise Conflict("That user is already on a team in this jam")
    if member_count(conn, team_id) > jam["max_team_size"]:
        raise BadRequest(f"Teams in this jam can have at most {jam['max_team_size']} members")
    conn.execute(
        "INSERT INTO team_members (team_id, user_id, joined_at) VALUES (?, ?, ?)",
        (team_id, user["id"], now_iso()),
    )
    conn.commit()
    return list_members(conn, team_id)


def remove_member(conn, team_id, user_id, removed_by):
    """Captains can remove anyone except themselves; members can leave."""
    team = get_team_or_404(conn, team_id)
    if removed_by["id"] not in (team["captain_id"], user_id):
        raise Forbidden("Only the captain can remove other members")
    if user_id == team["captain_id"]:
        raise BadRequest("The captain can't leave. Transfer captain first or delete the team.")
    if not is_member(conn, team_id, user_id):
        raise NotFound("That user is not on this team")
    conn.execute("DELETE FROM team_members WHERE team_id = ? AND user_id = ?", (team_id, user_id))
    conn.commit()
    return list_members(conn, team_id)


def transfer_captain(conn, team_id, new_captain_id, requested_by):
    team = get_team_or_404(conn, team_id)
    if requested_by["id"] != team["captain_id"]:
        raise Forbidden("Only the captain can hand over the captain role")
    if not is_member(conn, team_id, new_captain_id):
        raise BadRequest("The new captain must already be on the team")
    db.update(conn, "teams", team_id, {"captain_id": new_captain_id})
    return get_team_or_404(conn, team_id)


def team_detail(conn, team_id):
    team = get_team_or_404(conn, team_id)
    team["members"] = list_members(conn, team["id"])
    team["submission"] = db.fetch_one(
        conn, "SELECT id, title, submitted_at FROM submissions WHERE team_id = ?", (team_id,)
    )
    return team
