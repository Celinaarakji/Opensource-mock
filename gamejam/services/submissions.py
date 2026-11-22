"""Game submissions. Each team submits once and can edit while the jam is open."""

from gamejam import db
from gamejam.errors import Conflict, Forbidden, NotFound
from gamejam.services import jams, teams
from gamejam.utils.pagination import offset_for, paginate
from gamejam.utils.time import is_past_deadline, now_iso
from gamejam.validation import validate_submission


def create_submission(conn, team_id, body, user):
    team = teams.get_team_or_404(conn, team_id)
    jam = jams.get_jam(conn, team["jam_id"])
    jams.require_status(jam, "open")
    if not teams.is_member(conn, team_id, user["id"]):
        raise Forbidden("Only team members can submit for this team")
    if get_submission_for_team(conn, team_id):
        raise Conflict("This team already submitted. Edit the existing submission instead.")
    data = validate_submission(body)
    now = now_iso()
    data.update(
        {
            "team_id": team_id,
            "jam_id": jam["id"],
            "is_late": int(is_past_deadline(jam["deadline"], at=now)),
            "submitted_at": now,
            "updated_at": now,
        }
    )
    submission_id = db.insert(conn, "submissions", data)
    return get_submission(conn, submission_id)


def update_submission(conn, submission_id, body, user):
    submission = get_submission(conn, submission_id)
    jam = jams.get_jam(conn, submission["jam_id"])
    jams.require_status(jam, "open")
    if not teams.is_member(conn, submission["team_id"], user["id"]):
        raise Forbidden("Only team members can edit this submission")
    data = validate_submission(body, partial=True)
    now = now_iso()
    data["updated_at"] = now
    data["is_late"] = int(is_past_deadline(jam["deadline"], at=now))
    db.update(conn, "submissions", submission_id, data)
    return get_submission(conn, submission_id)


def get_submission(conn, submission_id):
    submission = db.fetch_one(
        conn,
        """
        SELECT s.*, t.name AS team_name
        FROM submissions s JOIN teams t ON t.id = s.team_id
        WHERE s.id = ?
        """,
        (submission_id,),
    )
    if submission is None:
        raise NotFound(f"Submission {submission_id} not found")
    submission["is_late"] = bool(submission["is_late"])
    return submission


def get_submission_for_team(conn, team_id):
    return db.fetch_one(conn, "SELECT * FROM submissions WHERE team_id = ?", (team_id,))


def list_submissions(conn, jam_id, page, limit, late=None):
    """A page of a jam's submissions, oldest first. `late` filters by lateness."""
    jams.get_jam(conn, jam_id)
    where = "s.jam_id = ?"
    params = [jam_id]
    if late is not None:
        where += " AND s.is_late = ?"
        params.append(int(late))
    total = conn.execute(
        f"SELECT COUNT(*) FROM submissions s WHERE {where}", params
    ).fetchone()[0]
    rows = db.fetch_all(
        conn,
        f"""
        SELECT s.id, s.title, s.team_id, t.name AS team_name, s.is_late, s.submitted_at
        FROM submissions s JOIN teams t ON t.id = s.team_id
        WHERE {where}
        ORDER BY s.submitted_at, s.id
        LIMIT ? OFFSET ?
        """,
        (*params, limit, offset_for(page, limit)),
    )
    for row in rows:
        row["is_late"] = bool(row["is_late"])
    return paginate(rows, page, limit, total=total)
