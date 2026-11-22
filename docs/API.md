# API Reference

Base URL when running locally: `http://localhost:8080`

All request and response bodies are JSON. Errors look like:

```json
{"error": "Validation failed", "details": {"email": "must be a valid email address"}}
```

## Authentication

Send `Authorization: Bearer <api_token>`. You get a token when you sign up
(`POST /users`). With `--seed`, demo tokens are `<username>-demo-token`, for
example `sam-demo-token` or `alex_org-demo-token`.

Routes marked 🔓 work without a token.

## Roles

| Role | Can |
|---|---|
| `organizer` | create jams, change status, add judges and criteria, see all scores, export CSV |
| `judge` | score submissions in jams they're assigned to |
| `participant` | create and join teams, submit games |

## General

| Method | Path | Notes |
|---|---|---|
| GET 🔓 | `/` | API name, version and the list of routes |
| GET 🔓 | `/health` | `{"status": "ok"}` |

## Users

| Method | Path | Notes |
|---|---|---|
| POST 🔓 | `/users` | Sign up. Body: `username`, `display_name`, `email`, optional `role`. Returns your `api_token`. |
| GET | `/users/me` | Your profile and the jams you're in |
| GET | `/users` | Organizers and judges only. Optional `?role=judge` |
| GET | `/users/{id}` | Public profile |

## Jams

| Method | Path | Notes |
|---|---|---|
| GET 🔓 | `/jams` | Optional `?status=open` |
| POST | `/jams` | Organizers. Body: `name`, `starts_at`, `deadline`, optional `theme`, `max_team_size` |
| GET 🔓 | `/jams/{id}` | Includes judges, criteria and team count |
| GET 🔓 | `/jams/by-slug/{slug}` | Same as above, by slug |
| POST | `/jams/{id}/status` | Organizers. Body: `{"status": "open"}` |
| GET 🔓 | `/jams/{id}/judges` | |
| POST | `/jams/{id}/judges` | Organizers. Body: `{"user_id": 2}` |
| GET 🔓 | `/jams/{id}/criteria` | |
| POST | `/jams/{id}/criteria` | Organizers. Body: `{"name": "Fun", "weight": 2}` |

Allowed status changes: `draft → open → judging → closed`, and
`judging → open` to reopen submissions.

## Teams

| Method | Path | Notes |
|---|---|---|
| GET 🔓 | `/jams/{id}/teams` | Includes `member_count` |
| GET | `/jams/{id}/teams.csv` | Organizers. CSV download |
| POST | `/jams/{id}/teams` | Body: `{"name": "Pixel Pirates"}`. You become captain. |
| GET 🔓 | `/teams/{id}` | Members and submission |
| POST | `/teams/{id}/members` | Captain only. Body: `{"username": "nora"}` |
| DELETE | `/teams/{id}/members/{user_id}` | Captain, or yourself to leave |
| POST | `/teams/{id}/captain` | Captain only. Body: `{"user_id": 5}` |

## Submissions

| Method | Path | Notes |
|---|---|---|
| POST | `/teams/{id}/submission` | Team members, while the jam is open. Body: `title`, optional `description`, `repo_url`, `demo_url` |
| GET 🔓 | `/submissions/{id}` | |
| PATCH | `/submissions/{id}` | Team members, while the jam is open |
| GET 🔓 | `/jams/{id}/submissions` | Paginated: `?page=1&limit=20`, optional `?late=true` |

Paginated responses look like:

```json
{"items": [...], "page": 1, "limit": 20, "total": 42, "pages": 3}
```

## Judging

| Method | Path | Notes |
|---|---|---|
| POST | `/submissions/{id}/scores` | Assigned judges, while the jam is judging. Body below. |
| GET | `/submissions/{id}/scores` | Judges see their own scores; organizers see all |
| GET | `/jams/{id}/judging/progress` | Judges: what you've scored so far |

```json
{"scores": [{"criterion_id": 1, "value": 8}, {"criterion_id": 2, "value": 6}],
 "comment": "Great use of the theme!"}
```

Scores are whole numbers from 1 to 10.

## Leaderboard

| Method | Path | Notes |
|---|---|---|
| GET 🔓 | `/jams/{id}/leaderboard` | Public once the jam is closed; organizers can see it earlier. `?include_unscored=true` |
| GET 🔓 | `/jams/{id}/winners` | Top 3 |

How the final score works: for each criterion, average all judges' scores, then
take the weighted average of those using the criteria weights. Teams with the
same score share the same rank.

## Search

| Method | Path | Notes |
|---|---|---|
| GET 🔓 | `/search?q=pixel` | Teams and submissions. Optional `&jam_id=1` |
