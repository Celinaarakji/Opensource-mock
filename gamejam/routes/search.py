"""Search route."""

from gamejam.errors import BadRequest
from gamejam.services import search


def register(router):
    @router.route("GET", "/search", auth=False)
    def do_search(req):
        term = req.query.get("q")
        if not term:
            raise BadRequest("Add ?q=<text> to search")
        jam_id = req.query.get("jam_id")
        if jam_id is not None and not jam_id.isdigit():
            raise BadRequest("jam_id must be a number")
        return search.search(req.conn, term, jam_id=jam_id)
