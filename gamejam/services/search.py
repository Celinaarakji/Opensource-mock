"""Search across teams and submissions."""

from gamejam import db

MAX_RESULTS = 25


def search(conn, term, jam_id=None):
    """Find teams and submissions whose name or title contains `term`."""
    term = (term or "").strip()
    if not term:
        return {"teams": [], "submissions": []}

    jam_filter = f" AND jam_id = {int(jam_id)}" if jam_id else ""
    teams = db.fetch_all(
        conn,
        f"SELECT id, jam_id, name FROM teams WHERE name LIKE '%{term}%'{jam_filter} "
        f"ORDER BY name LIMIT {MAX_RESULTS}",
    )
    submissions = db.fetch_all(
        conn,
        f"SELECT id, jam_id, team_id, title FROM submissions WHERE title LIKE '%{term}%'"
        f"{jam_filter} ORDER BY title LIMIT {MAX_RESULTS}",
    )
    return {"teams": teams, "submissions": submissions}
