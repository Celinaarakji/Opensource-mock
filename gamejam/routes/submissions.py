"""Submission routes."""

from gamejam.errors import BadRequest
from gamejam.services import submissions
from gamejam.utils.pagination import get_page_params


def _parse_bool(value):
    if value is None:
        return None
    if value.lower() in ("true", "1", "yes"):
        return True
    if value.lower() in ("false", "0", "no"):
        return False
    raise BadRequest("late must be true or false")


def register(router):
    @router.route("POST", "/teams/{team_id:int}/submission")
    def create_submission(req):
        return 201, submissions.create_submission(
            req.conn, req.params["team_id"], req.json, req.user
        )

    @router.route("GET", "/submissions/{submission_id:int}", auth=False)
    def get_submission(req):
        return submissions.get_submission(req.conn, req.params["submission_id"])

    @router.route("PATCH", "/submissions/{submission_id:int}")
    def update_submission(req):
        return submissions.update_submission(
            req.conn, req.params["submission_id"], req.json, req.user
        )

    @router.route("GET", "/jams/{jam_id:int}/submissions", auth=False)
    def list_submissions(req):
        page, limit = get_page_params(req.query)
        late = _parse_bool(req.query.get("late"))
        return submissions.list_submissions(req.conn, req.params["jam_id"], page, limit, late)
