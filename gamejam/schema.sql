-- Game Jam API database schema (SQLite)

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    display_name  TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    role          TEXT NOT NULL CHECK (role IN ('organizer', 'judge', 'participant')),
    api_token     TEXT NOT NULL UNIQUE,
    created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS jams (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT NOT NULL,
    slug           TEXT NOT NULL UNIQUE,
    theme          TEXT,
    starts_at      TEXT NOT NULL,
    deadline       TEXT NOT NULL,
    max_team_size  INTEGER NOT NULL DEFAULT 4,
    status         TEXT NOT NULL DEFAULT 'draft',
    created_by     INTEGER NOT NULL REFERENCES users(id),
    created_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS jam_judges (
    jam_id   INTEGER NOT NULL REFERENCES jams(id) ON DELETE CASCADE,
    user_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    PRIMARY KEY (jam_id, user_id)
);

CREATE TABLE IF NOT EXISTS teams (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    jam_id      INTEGER NOT NULL REFERENCES jams(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    captain_id  INTEGER NOT NULL REFERENCES users(id),
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS team_members (
    team_id    INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    joined_at  TEXT NOT NULL,
    PRIMARY KEY (team_id, user_id)
);

CREATE TABLE IF NOT EXISTS submissions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id       INTEGER NOT NULL UNIQUE REFERENCES teams(id) ON DELETE CASCADE,
    jam_id        INTEGER NOT NULL REFERENCES jams(id) ON DELETE CASCADE,
    title         TEXT NOT NULL,
    description   TEXT,
    repo_url      TEXT,
    demo_url      TEXT,
    is_late       INTEGER NOT NULL DEFAULT 0,
    submitted_at  TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS criteria (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    jam_id  INTEGER NOT NULL REFERENCES jams(id) ON DELETE CASCADE,
    name    TEXT NOT NULL,
    weight  REAL NOT NULL DEFAULT 1.0
);

CREATE TABLE IF NOT EXISTS scores (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id  INTEGER NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
    judge_id       INTEGER NOT NULL REFERENCES users(id),
    criterion_id   INTEGER NOT NULL REFERENCES criteria(id) ON DELETE CASCADE,
    value          INTEGER NOT NULL,
    comment        TEXT,
    created_at     TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_teams_jam ON teams(jam_id);
CREATE INDEX IF NOT EXISTS idx_submissions_jam ON submissions(jam_id);
CREATE INDEX IF NOT EXISTS idx_scores_submission ON scores(submission_id);
