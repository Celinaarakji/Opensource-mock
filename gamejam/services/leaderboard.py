"""Leaderboard: turns raw judge scores into a ranked list.

For each submission:
  1. Average every judge's score per criterion.
  2. Combine those averages using the criteria weights.
  3. Rank submissions from highest to lowest final score.
"""

from collections import defaultdict

from gamejam import db
from gamejam.services import jams
from gamejam.utils.formatting import round_score


def _average(values):
    if not values:
        return None
    return sum(values) // len(values)


def _weighted(criterion_averages, weights):
    """Combine {criterion_id: average} using {criterion_id: weight}."""
    total = 0.0
    total_weight = 0.0
    for criterion_id, average in criterion_averages.items():
        if average is None:
            continue
        weight = weights.get(criterion_id, 1.0)
        total += average * weight
        total_weight += weight
    if total_weight == 0:
        return None
    return total / total_weight


def _load_scores(conn, jam_id):
    """{submission_id: {criterion_id: [values...]}} for one jam."""
    rows = db.fetch_all(
        conn,
        """
        SELECT sc.submission_id, sc.criterion_id, sc.value
        FROM scores sc JOIN submissions s ON s.id = sc.submission_id
        WHERE s.jam_id = ?
        """,
        (jam_id,),
    )
    grouped = defaultdict(lambda: defaultdict(list))
    for row in rows:
        grouped[row["submission_id"]][row["criterion_id"]].append(row["value"])
    return grouped


def compute_leaderboard(conn, jam_id, include_unscored=False):
    jams.get_jam(conn, jam_id)
    weights = {c["id"]: c["weight"] for c in jams.list_criteria(conn, jam_id)}
    scores = _load_scores(conn, jam_id)
    submissions = db.fetch_all(
        conn,
        """
        SELECT s.id, s.title, s.is_late, t.id AS team_id, t.name AS team_name
        FROM submissions s JOIN teams t ON t.id = s.team_id
        WHERE s.jam_id = ?
        """,
        (jam_id,),
    )

    entries = []
    for sub in submissions:
        per_criterion = {cid: _average(vals) for cid, vals in scores.get(sub["id"], {}).items()}
        final = _weighted(per_criterion, weights)
        if final is None and not include_unscored:
            continue
        entries.append(
            {
                "submission_id": sub["id"],
                "title": sub["title"],
                "team_id": sub["team_id"],
                "team_name": sub["team_name"],
                "is_late": bool(sub["is_late"]),
                "criteria": {str(k): round_score(v) for k, v in per_criterion.items()},
                "score": round_score(final),
            }
        )

    entries.sort(key=lambda e: (e["score"] is None, -(e["score"] or 0)))
    for position, entry in enumerate(entries, start=1):
        entry["rank"] = position if entry["score"] is not None else None
    return entries


def winners(conn, jam_id, count=3):
    """The top `count` entries of the leaderboard."""
    return compute_leaderboard(conn, jam_id)[:count]
