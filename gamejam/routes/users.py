"""User routes."""

from gamejam import auth, config
from gamejam.services import users


def register(router):
    @router.route("POST", "/users", auth=False)
    def create_user(req):
        """Sign up. The response includes your api_token: keep it safe."""
        user = users.create_user(req.conn, req.json)
        return 201, user

    @router.route("GET", "/users/me")
    def me(req):
        profile = auth.public_user(req.user)
        profile["email"] = req.user["email"]
        profile["jams"] = users.user_jams(req.conn, req.user["id"])
        return profile

    @router.route("GET", "/users")
    def list_users(req):
        auth.require_role(req.user, config.ROLE_ORGANIZER, config.ROLE_JUDGE)
        return users.list_users(req.conn, role=req.query.get("role"))

    @router.route("GET", "/users/{user_id:int}")
    def get_user(req):
        return auth.public_user(users.get_user(req.conn, req.params["user_id"]))
