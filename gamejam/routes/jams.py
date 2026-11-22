"""Jam routes: create jams, change status, judges and criteria."""

from gamejam import auth, config
from gamejam.errors import BadRequest
from gamejam.services import jams, users


def register(router):
    @router.route("GET", "/jams", auth=False)
    def list_jams(req):
        return jams.list_jams(req.conn, status=req.query.get("status"))

    @router.route("POST", "/jams")
    def create_jam(req):
        auth.require_role(req.user, config.ROLE_ORGANIZER)
        return 201, jams.create_jam(req.conn, req.json, req.user)

    @router.route("GET", "/jams/{jam_id:int}", auth=False)
    def get_jam(req):
        return jams.jam_detail(req.conn, req.params["jam_id"])

    @router.route("GET", "/jams/by-slug/{slug}", auth=False)
    def get_jam_by_slug(req):
        jam = jams.get_jam_by_slug(req.conn, req.params["slug"])
        if jam is None:
            from gamejam.errors import NotFound
            raise NotFound("No jam with that slug")
        return jams.jam_detail(req.conn, jam["id"])

    @router.route("POST", "/jams/{jam_id:int}/status")
    def set_status(req):
        auth.require_role(req.user, config.ROLE_ORGANIZER)
        status = req.json.get("status")
        if not status:
            raise BadRequest("Send {\"status\": \"open\"} (or judging / closed)")
        return jams.set_status(req.conn, req.params["jam_id"], status)

    @router.route("GET", "/jams/{jam_id:int}/judges", auth=False)
    def list_judges(req):
        jams.get_jam(req.conn, req.params["jam_id"])
        return jams.list_judges(req.conn, req.params["jam_id"])

    @router.route("POST", "/jams/{jam_id:int}/judges")
    def add_judge(req):
        auth.require_role(req.user, config.ROLE_ORGANIZER)
        user_id = req.json.get("user_id")
        if not isinstance(user_id, int):
            raise BadRequest("Send {\"user_id\": <id>}")
        judge = users.get_user(req.conn, user_id)
        jams.add_judge(req.conn, req.params["jam_id"], judge)
        return 201, jams.list_judges(req.conn, req.params["jam_id"])

    @router.route("GET", "/jams/{jam_id:int}/criteria", auth=False)
    def list_criteria(req):
        jams.get_jam(req.conn, req.params["jam_id"])
        return jams.list_criteria(req.conn, req.params["jam_id"])

    @router.route("POST", "/jams/{jam_id:int}/criteria")
    def add_criterion(req):
        auth.require_role(req.user, config.ROLE_ORGANIZER)
        return 201, jams.add_criterion(req.conn, req.params["jam_id"], req.json)
