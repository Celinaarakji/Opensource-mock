"""Builds the router with every route registered."""

from gamejam import __version__
from gamejam.router import Router
from gamejam.routes import register_all


def create_router():
    router = Router()

    @router.route("GET", "/", auth=False)
    def index(req):
        return {
            "name": "Game Jam API",
            "version": __version__,
            "routes": router.describe(),
        }

    @router.route("GET", "/health", auth=False)
    def health(req):
        req.conn.execute("SELECT 1")
        return {"status": "ok"}

    register_all(router)
    return router
