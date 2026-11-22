"""Configuration for the Game Jam API.

Values can be overridden with environment variables so you never have to
edit this file to run the server locally.
"""

import os

# Where the SQLite database lives. Use ":memory:" for throwaway runs.
DB_PATH = os.environ.get("GAMEJAM_DB", "gamejam.db")

# Server settings
HOST = os.environ.get("GAMEJAM_HOST", "127.0.0.1")
PORT = int(os.environ.get("GAMEJAM_PORT", "8080"))

# Judging
MIN_SCORE = 1
MAX_SCORE = 10

# Teams
DEFAULT_MAX_TEAM_SIZE = 4

# Pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Roles a user can have
ROLE_ORGANIZER = "organizer"
ROLE_JUDGE = "judge"
ROLE_PARTICIPANT = "participant"
ROLES = (ROLE_ORGANIZER, ROLE_JUDGE, ROLE_PARTICIPANT)

# Jam lifecycle
JAM_STATUSES = ("draft", "open", "judging", "closed")
