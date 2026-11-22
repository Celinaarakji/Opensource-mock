"""Jams: the events teams compete in."""

from gamejam import config, db
from gamejam.errors import BadRequest, Conflict, NotFound
from gamejam.utils.text import slugify
from gamejam.utils.time import humanize_delta, is_past_deadline, now_iso, time_left
from gamejam.validation import validate_criterion, validate_jam

# Which status a jam may move to from each status.
ALLOWED_TRANSITIONS = {
    "draft": {"open"},
    "open": {"judging"},
    "judging": {"closed", "open"},
    "closed": set(),
}


def create_jam(conn, body, organizer):
    data = validate_jam(body)
    data["slug"] = slugify(data["name"])
    if not data["slug"]:
        raise BadRequest("Jam name needs at least one letter or number")
    if get_jam_by_slug(conn, data["slug"]):
        raise Conflict("A jam with that name already exists")
    data["status"] = "draft"
    data["created_by"] = organizer["id"]
    data["created_at"] = now_iso()
    jam_id = db.insert(conn, "jams", data)
    return get_jam(conn, jam_id)


def get_jam(conn, jam_id):
    jam = db.fetch_one(conn, "SELECT * FROM jams WHERE id = ?", (jam_id,))
    if jam is None:
        raise NotFound(f"Jam {jam_id} not found")
    return jam


def get_jam_by_slug(conn, slug):
    return db.fetch_one(conn, "SELECT * FROM jams WHERE slug = ?", (slug,))


def list_jams(conn, status=None):
    if status:
        if status not in config.JAM_STATUSES:
            raise BadRequest(f"status must be one of {', '.join(config.JAM_STATUSES)}")
        return db.fetch_all(
            conn, "SELECT * FROM jams WHERE status = ? ORDER BY starts_at DESC", (status,)
        )
    return db.fetch_all(conn, "SELECT * FROM jams ORDER BY starts_at DESC")


def set_status(conn, jam_id, new_status):
    jam = get_jam(conn, jam_id)
    if new_status not in config.JAM_STATUSES:
        raise BadRequest(f"status must be one of {', '.join(config.JAM_STATUSES)}")
    if new_status not in ALLOWED_TRANSITIONS[jam["status"]]:
        raise BadRequest(f"Can't move a jam from {jam['status']} to {new_status}")
    db.update(conn, "jams", jam_id, {"status": new_status})
    return get_jam(conn, jam_id)


def require_status(jam, *statuses):
    if jam["status"] not in statuses:
        raise BadRequest(
            f"This jam is {jam['status']}; that only works while it is {' or '.join(statuses)}"
        )


# --- Judges -----------------------------------------------------------------

def add_judge(conn, jam_id, user):
    get_jam(conn, jam_id)
    if user["role"] != config.ROLE_JUDGE:
        raise BadRequest("Only users with the judge role can judge a jam")
    if is_judge(conn, jam_id, user["id"]):
        raise Conflict("That user already judges this jam")
    conn.execute("INSERT INTO jam_judges (jam_id, user_id) VALUES (?, ?)", (jam_id, user["id"]))
    conn.commit()


def is_judge(conn, jam_id, user_id):
    row = db.fetch_one(
        conn, "SELECT 1 AS ok FROM jam_judges WHERE jam_id = ? AND user_id = ?", (jam_id, user_id)
    )
    return row is not None


def list_judges(conn, jam_id):
    return db.fetch_all(
        conn,
        """
        SELECT u.id, u.username, u.display_name
        FROM jam_judges jj JOIN users u ON u.id = jj.user_id
        WHERE jj.jam_id = ? ORDER BY u.display_name
        """,
        (jam_id,),
    )


# --- Criteria ---------------------------------------------------------------

def add_criterion(conn, jam_id, body):
    jam = get_jam(conn, jam_id)
    require_status(jam, "draft", "open")
    data = validate_criterion(body)
    data["jam_id"] = jam_id
    criterion_id = db.insert(conn, "criteria", data)
    return db.fetch_one(conn, "SELECT * FROM criteria WHERE id = ?", (criterion_id,))


def list_criteria(conn, jam_id):
    return db.fetch_all(conn, "SELECT * FROM criteria WHERE jam_id = ? ORDER BY id", (jam_id,))


def get_criterion(conn, jam_id, criterion_id):
    criterion = db.fetch_one(
        conn, "SELECT * FROM criteria WHERE id = ? AND jam_id = ?", (criterion_id, jam_id)
    )
    if criterion is None:
        raise NotFound(f"Criterion {criterion_id} is not part of jam {jam_id}")
    return criterion


def jam_detail(conn, jam_id):
    """A jam plus its judges and criteria, for GET /jams/{id}."""
    jam = get_jam(conn, jam_id)
    jam["judges"] = list_judges(conn, jam_id)
    jam["criteria"] = list_criteria(conn, jam_id)
    jam["team_count"] = conn.execute(
        "SELECT COUNT(*) FROM teams WHERE jam_id = ?", (jam_id,)
    ).fetchone()[0]
    jam["time_left"] = humanize_delta(time_left(jam["deadline"]))
    jam["is_past_deadline"] = is_past_deadline(jam["deadline"])
    return jam
