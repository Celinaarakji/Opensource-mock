"""Leaderboard routes."""

from gamejam import auth, config
from gamejam.errors import Forbidden
from gamejam.services import jams, leaderboard


def register(router):
    @router.route("GET", "/jams/{jam_id:int}/leaderboard", auth=False)
    def get_leaderboard(req):
        jam = jams.get_jam(req.conn, req.params["jam_id"])
        # Results stay hidden until the jam is closed, except for organizers.
        if jam["status"] != "closed":
            if req.user is None or req.user["role"] != config.ROLE_ORGANIZER:
                raise Forbidden("The leaderboard is published when the jam closes")
        include_unscored = req.query.get("include_unscored") == "true"
        return leaderboard.compute_leaderboard(req.conn, jam["id"], include_unscored)

    @router.route("GET", "/jams/{jam_id:int}/winners", auth=False)
    def get_winners(req):
        jam = jams.get_jam(req.conn, req.params["jam_id"])
        if jam["status"] != "closed":
            auth.require_role(req.user, config.ROLE_ORGANIZER)
        return leaderboard.winners(req.conn, jam["id"])
