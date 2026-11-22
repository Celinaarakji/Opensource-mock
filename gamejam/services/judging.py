"""Judging: judges score each submission on the jam's criteria."""

from gamejam import config, db
from gamejam.errors import BadRequest, Forbidden
from gamejam.services import jams, submissions, teams
from gamejam.utils.time import now_iso
from gamejam.validation import validate_scores


def check_can_judge(conn, jam, judge):
    if judge["role"] != config.ROLE_JUDGE:
        raise Forbidden("Only judges can score submissions")
    if not jams.is_judge(conn, jam["id"], judge["id"]):
        raise Forbidden("You are not a judge for this jam")


def check_conflict_of_interest(conn, submission, judge):
    """A judge must never score a team they are connected to."""
    team = teams.get_team_or_404(conn, submission["team_id"])
    if team["captain_id"] == judge["id"]:
        raise Forbidden("You can't judge your own team")


def submit_scores(conn, submission_id, body, judge):
    """Record one judge's scores for a submission.

    Body: {"scores": [{"criterion_id": 1, "value": 8}, ...], "comment": "Fun!"}
    """
    submission = submissions.get_submission(conn, submission_id)
    jam = jams.get_jam(conn, submission["jam_id"])
    jams.require_status(jam, "judging")
    check_can_judge(conn, jam, judge)
    check_conflict_of_interest(conn, submission, judge)
    data = validate_scores(body)

    criteria_ids = {c["id"] for c in jams.list_criteria(conn, jam["id"])}
    for entry in data["scores"]:
        if entry["criterion_id"] not in criteria_ids:
            raise BadRequest(f"Criterion {entry['criterion_id']} is not part of this jam")

    now = now_iso()
    for entry in data["scores"]:
        conn.execute(
            """
            INSERT INTO scores (submission_id, judge_id, criterion_id, value, comment, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (submission_id, judge["id"], entry["criterion_id"], entry["value"],
             data.get("comment"), now),
        )
    conn.commit()
    return scores_by_judge(conn, submission_id, judge["id"])


def scores_by_judge(conn, submission_id, judge_id):
    return db.fetch_all(
        conn,
        """
        SELECT sc.criterion_id, c.name AS criterion, sc.value, sc.comment, sc.created_at
        FROM scores sc JOIN criteria c ON c.id = sc.criterion_id
        WHERE sc.submission_id = ? AND sc.judge_id = ?
        ORDER BY sc.criterion_id
        """,
        (submission_id, judge_id),
    )


def all_scores(conn, submission_id):
    """Every score for a submission. Organizers only: judges see their own."""
    return db.fetch_all(
        conn,
        """
        SELECT sc.judge_id, u.display_name AS judge, sc.criterion_id, c.name AS criterion,
               sc.value, sc.comment
        FROM scores sc
        JOIN criteria c ON c.id = sc.criterion_id
        JOIN users u ON u.id = sc.judge_id
        WHERE sc.submission_id = ?
        ORDER BY sc.judge_id, sc.criterion_id
        """,
        (submission_id,),
    )


def judge_progress(conn, jam_id, judge_id):
    """Which submissions a judge has scored and which are still to do."""
    rows = db.fetch_all(
        conn,
        """
        SELECT s.id, s.title, t.name AS team_name,
               EXISTS (SELECT 1 FROM scores sc
                       WHERE sc.submission_id = s.id AND sc.judge_id = ?) AS scored
        FROM submissions s JOIN teams t ON t.id = s.team_id
        WHERE s.jam_id = ?
        ORDER BY s.id
        """,
        (judge_id, jam_id),
    )
    for row in rows:
        row["scored"] = bool(row["scored"])
    done = sum(1 for r in rows if r["scored"])
    return {"done": done, "total": len(rows), "submissions": rows}
