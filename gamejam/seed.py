"""Demo data so there is something to look at right away.

Run with `python -m gamejam --seed`. This WIPES the database first.

Tokens are fixed and printed on startup so you can try requests quickly.
Never use fixed tokens like these outside local development.
"""

from gamejam import db

TABLES = ["scores", "criteria", "submissions", "team_members", "teams", "jam_judges", "jams",
          "users"]

USERS = [
    ("alex_org", "Alex Rivera", "organizer"),
    ("maya_judge", "Maya Chen", "judge"),
    ("omar_judge", "Omar Haddad", "judge"),
    ("sam", "Sam Okafor", "participant"),
    ("priya", "Priya Nair", "participant"),
    ("leo", "Leo Martin", "participant"),
    ("nora", "Nora Kim", "participant"),
    ("jay", "Jay Patel", "participant"),
    ("ana", "Ana Souza", "participant"),
    ("ben", "Ben Tremblay", "participant"),
    ("zoe", "Zoe Wright", "participant"),
    ("tom", "Tom Nguyen", "participant"),
    ("lina", "Lina Haddad", "participant"),
]

JAMS = [
    {
        "name": "Winter Game Jam 2026",
        "slug": "winter-game-jam-2026",
        "theme": "Everything is frozen",
        "starts_at": "2026-12-04T18:00:00-05:00",
        "deadline": "2026-12-06T23:59:00-05:00",
        "max_team_size": 4,
        "status": "closed",
    },
    {
        "name": "Spring Mini Jam 2027",
        "slug": "spring-mini-jam-2027",
        "theme": "Growth",
        "starts_at": "2027-03-12T18:00:00-04:00",
        "deadline": "2027-03-14T23:59:00-04:00",
        "max_team_size": 3,
        "status": "open",
    },
    {
        "name": "Summer Jam 2027",
        "slug": "summer-jam-2027",
        "theme": None,
        "starts_at": "2027-07-09T18:00:00-04:00",
        "deadline": "2027-07-11T23:59:00-04:00",
        "max_team_size": 4,
        "status": "draft",
    },
]

# (jam slug, team name, [members, captain first])
TEAMS = [
    ("winter-game-jam-2026", "Pixel Pirates", ["sam", "priya"]),
    ("winter-game-jam-2026", "Byte Knights", ["leo", "nora", "jay"]),
    ("winter-game-jam-2026", "Lag Monsters", ["ana", "ben"]),
    ("winter-game-jam-2026", "Null Pointers", ["zoe"]),
    ("winter-game-jam-2026", "Quest Crafters", ["tom", "lina"]),
    ("spring-mini-jam-2027", "Sprout Squad", ["sam", "leo"]),
    ("spring-mini-jam-2027", "Bloom Bots", ["priya"]),
]

# (team name, title, description, submitted_at UTC, is_late)
SUBMISSIONS = [
    ("Pixel Pirates", "Ice Floe Escape", "Hop between melting ice floes.",
     "2026-12-07T02:30:00+00:00", 0),
    ("Byte Knights", "Frostbite Fortress", "Tower defence in a frozen castle.",
     "2026-12-07T01:15:00+00:00", 0),
    ("Lag Monsters", "Snowball Rush", "Roll a snowball downhill without melting it.",
     "2026-12-07T03:45:00+00:00", 0),
    ("Null Pointers", "Frozen Time", "Stop time to solve puzzles.",
     "2026-12-07T06:10:00+00:00", 1),
    ("Quest Crafters", "The Last Thaw", "A short RPG about bringing spring back.",
     "2026-12-06T23:05:00+00:00", 0),
    ("Sprout Squad", "Seedling", "Grow a plant by solving light puzzles.",
     "2027-03-13T20:00:00+00:00", 0),
]

CRITERIA = {
    "winter-game-jam-2026": [("Fun", 2.0), ("Theme", 1.0), ("Polish", 1.0)],
    "spring-mini-jam-2027": [("Fun", 1.0), ("Creativity", 1.0)],
}

JUDGES = {
    "winter-game-jam-2026": ["maya_judge", "omar_judge"],
    "spring-mini-jam-2027": ["maya_judge"],
}

# team name -> {criterion: (maya's score, omar's score)}
WINTER_SCORES = {
    "Pixel Pirates": {"Fun": (8, 7), "Theme": (9, 8), "Polish": (7, 7)},
    "Byte Knights": {"Fun": (7, 7), "Theme": (8, 8), "Polish": (8, 7)},
    "Lag Monsters": {"Fun": (9, 8), "Theme": (6, 7), "Polish": (6, 6)},
    "Null Pointers": {"Fun": (6, 5), "Theme": (7, 7), "Polish": (5, 6)},
    "Quest Crafters": {"Fun": (10, 9), "Theme": (5, 6), "Polish": (4, 5)},
}

CREATED_AT = "2026-11-01T12:00:00+00:00"


def token_for(username):
    return f"{username}-demo-token"


def reset(conn):
    for table in TABLES:
        conn.execute(f"DROP TABLE IF EXISTS {table}")
    conn.commit()
    db.init_db(conn)


def seed(conn):
    """Wipe the database and load demo data. Returns {username: token}."""
    reset(conn)
    users = {}
    for username, name, role in USERS:
        users[username] = db.insert(conn, "users", {
            "username": username,
            "display_name": name,
            "email": f"{username}@example.com",
            "role": role,
            "api_token": token_for(username),
            "created_at": CREATED_AT,
        })

    jams = {}
    for jam in JAMS:
        jams[jam["slug"]] = db.insert(
            conn, "jams", {**jam, "created_by": users["alex_org"], "created_at": CREATED_AT}
        )

    for slug, judges in JUDGES.items():
        for username in judges:
            conn.execute("INSERT INTO jam_judges (jam_id, user_id) VALUES (?, ?)",
                         (jams[slug], users[username]))

    criteria = {}
    for slug, items in CRITERIA.items():
        for name, weight in items:
            criteria[(slug, name)] = db.insert(
                conn, "criteria", {"jam_id": jams[slug], "name": name, "weight": weight}
            )

    teams = {}
    for slug, team_name, members in TEAMS:
        team_id = db.insert(conn, "teams", {
            "jam_id": jams[slug],
            "name": team_name,
            "captain_id": users[members[0]],
            "created_at": CREATED_AT,
        })
        teams[team_name] = (team_id, slug)
        for username in members:
            conn.execute(
                "INSERT INTO team_members (team_id, user_id, joined_at) VALUES (?, ?, ?)",
                (team_id, users[username], CREATED_AT),
            )

    submissions = {}
    for team_name, title, description, submitted_at, is_late in SUBMISSIONS:
        team_id, slug = teams[team_name]
        submissions[team_name] = db.insert(conn, "submissions", {
            "team_id": team_id,
            "jam_id": jams[slug],
            "title": title,
            "description": description,
            "repo_url": f"https://github.com/example/{title.lower().replace(' ', '-')}",
            "is_late": is_late,
            "submitted_at": submitted_at,
            "updated_at": submitted_at,
        })

    for team_name, per_criterion in WINTER_SCORES.items():
        for criterion, (maya, omar) in per_criterion.items():
            for judge, value in (("maya_judge", maya), ("omar_judge", omar)):
                conn.execute(
                    """
                    INSERT INTO scores (submission_id, judge_id, criterion_id, value, comment,
                                        created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (submissions[team_name], users[judge],
                     criteria[("winter-game-jam-2026", criterion)], value, None,
                     "2026-12-08T15:00:00+00:00"),
                )
    conn.commit()
    return {username: token_for(username) for username, _, _ in USERS}
