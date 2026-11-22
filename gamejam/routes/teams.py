"""Team routes."""

from gamejam import auth, config
from gamejam.errors import BadRequest
from gamejam.services import teams, users
from gamejam.utils.formatting import to_csv
from gamejam.web import Response

TEAM_CSV_COLUMNS = ["id", "name", "captain_id", "member_count", "created_at"]


def register(router):
    @router.route("GET", "/jams/{jam_id:int}/teams", auth=False)
    def list_teams(req):
        return teams.list_teams(req.conn, req.params["jam_id"])

    @router.route("GET", "/jams/{jam_id:int}/teams.csv")
    def export_teams(req):
        auth.require_role(req.user, config.ROLE_ORGANIZER)
        rows = teams.list_teams(req.conn, req.params["jam_id"])
        return Response(
            to_csv(rows, TEAM_CSV_COLUMNS),
            content_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=teams.csv"},
        )

    @router.route("POST", "/jams/{jam_id:int}/teams")
    def create_team(req):
        return 201, teams.create_team(req.conn, req.params["jam_id"], req.json, req.user)

    @router.route("GET", "/teams/{team_id:int}", auth=False)
    def get_team(req):
        return teams.team_detail(req.conn, req.params["team_id"])

    @router.route("POST", "/teams/{team_id:int}/members")
    def add_member(req):
        username = req.json.get("username")
        if not username:
            raise BadRequest("Send {\"username\": \"...\"}")
        user = users.get_user_by_username(req.conn, username)
        if user is None:
            raise BadRequest(f"No user called {username}")
        return 201, teams.add_member(req.conn, req.params["team_id"], user, req.user)

    @router.route("DELETE", "/teams/{team_id:int}/members/{user_id:int}")
    def remove_member(req):
        return teams.remove_member(
            req.conn, req.params["team_id"], req.params["user_id"], req.user
        )

    @router.route("POST", "/teams/{team_id:int}/captain")
    def transfer_captain(req):
        user_id = req.json.get("user_id")
        if not isinstance(user_id, int):
            raise BadRequest("Send {\"user_id\": <id>}")
        return teams.transfer_captain(req.conn, req.params["team_id"], user_id, req.user)
