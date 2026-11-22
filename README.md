# 🎮 Game Jam API

A small backend for running game jams: organizers create jams, participants form
teams and submit games, judges score them, and everyone sees the leaderboard
when the jam closes.

It's written in plain Python with **no dependencies**: just the standard
library (`http.server`, `sqlite3`, `unittest`).

## Features

- Jams with a lifecycle: `draft` → `open` → `judging` → `closed`
- Teams with captains and a size limit per jam
- One submission per team, editable until judging starts
- Weighted judging criteria (for example Fun ×2, Theme ×1, Polish ×1)
- A leaderboard that is hidden until the jam closes
- Search across teams and submissions
- CSV export of teams for organizers

## Getting started

You need **Python 3.10 or newer**.

```bash
git clone https://github.com/Celinaarakji/Opensource-mock.git
cd Opensource-mock
pip install -r requirements.txt
python main.py --seed
```

The API is now running on http://localhost:8000.

`--seed` resets the database and loads demo data: three jams, five teams with
judged submissions, and a set of users. The demo tokens are printed when the
server starts.

## Trying it out

```bash
# Public: list jams
curl http://localhost:8000/jams

# The leaderboard of the closed Winter jam
curl http://localhost:8000/jams/1/leaderboard

# Authenticated: who am I?
curl -H "Authorization: Bearer sam-demo-token" http://localhost:8000/users/me
```

See [docs/API.md](docs/API.md) for every endpoint.

## Running the tests

```bash
python -m unittest discover -s tests -t .
```

If you have `pytest` installed, `pytest` works too.

## Project layout

```
gamejam/
  __main__.py      starts the server (python -m gamejam)
  app.py           builds the router
  web.py           request/response objects and the HTTP server
  router.py        URL routing
  auth.py          bearer tokens and role checks
  validation.py    request body validation
  db.py            SQLite helpers
  schema.sql       database tables
  seed.py          demo data
  routes/          thin HTTP handlers, one file per area
  services/        business logic (this is where most changes go)
  utils/           shared helpers: time, text, pagination, formatting
tests/             unittest test suite
docs/              API reference
```

## Contributing

We'd love your help! Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a
pull request, and look for issues labelled `good first issue`.

Found a security problem? **Don't open a public issue.** See
[SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE)
