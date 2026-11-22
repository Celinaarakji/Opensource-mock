"""Judging routes."""

from gamejam import auth, config
from gamejam.services import jams, judging, submissions


def register(router):
    @router.route("POST", "/submissions/{submission_id:int}/scores")
    def submit_scores(req):
        return 201, judging.submit_scores(
            req.conn, req.params["submission_id"], req.json, req.user
        )

    @router.route("GET", "/submissions/{submission_id:int}/scores")
    def get_scores(req):
        submission_id = req.params["submission_id"]
        submissions.get_submission(req.conn, submission_id)
        if req.user["role"] == config.ROLE_ORGANIZER:
            return judging.all_scores(req.conn, submission_id)
        auth.require_role(req.user, config.ROLE_JUDGE)
        return judging.scores_by_judge(req.conn, submission_id, req.user["id"])

    @router.route("GET", "/jams/{jam_id:int}/judging/progress")
    def progress(req):
        jam = jams.get_jam(req.conn, req.params["jam_id"])
        auth.require_role(req.user, config.ROLE_JUDGE)
        judging.check_can_judge(req.conn, jam, req.user)
        return judging.judge_progress(req.conn, jam["id"], req.user["id"])
