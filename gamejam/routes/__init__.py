"""HTTP routes. Each module exposes `register(router)`."""

from gamejam.routes import jams, judging, leaderboard, search, submissions, teams, users

ALL = (users, jams, teams, submissions, judging, leaderboard, search)


def register_all(router):
    for module in ALL:
        module.register(router)
