"""End-to-end tests through the router (no real server needed)."""

import unittest

from tests.helpers import ApiClient, make_conn


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.api = ApiClient(make_conn())
        self.addCleanup(self.api.conn.close)

    def test_health(self):
        self.assertEqual(self.api.get("/health"), (200, {"status": "ok"}))

    def test_index_lists_routes(self):
        status, body = self.api.get("/")
        self.assertEqual(status, 200)
        self.assertIn({"method": "GET", "path": "/health", "auth": False}, body["routes"])

    def test_unknown_route(self):
        self.assertEqual(self.api.get("/nope")[0], 404)

    def test_wrong_method(self):
        self.assertEqual(self.api.delete("/jams")[0], 405)

    def test_auth_required(self):
        self.assertEqual(self.api.get("/users/me")[0], 401)

    def test_me(self):
        status, body = self.api.get("/users/me", as_user="sam")
        self.assertEqual(status, 200)
        self.assertEqual(body["username"], "sam")
        self.assertEqual(len(body["jams"]), 2)

    def test_sign_up(self):
        status, body = self.api.post(
            "/users", {"username": "newbie", "display_name": "New Bie", "email": "n@b.ca"}
        )
        self.assertEqual(status, 201)
        self.assertTrue(body["api_token"])

    def test_sign_up_validation(self):
        status, body = self.api.post("/users", {"username": "x"})
        self.assertEqual(status, 400)
        self.assertIn("email", body["details"])

    def test_public_user_hides_email(self):
        status, body = self.api.get("/users/4", as_user="priya")
        self.assertEqual(status, 200)
        self.assertNotIn("email", body)

    def test_only_organizers_create_jams(self):
        jam = {"name": "Fall Jam", "starts_at": "2027-10-01T18:00:00Z",
               "deadline": "2027-10-03T23:59:00Z"}
        self.assertEqual(self.api.post("/jams", jam, as_user="sam")[0], 403)
        status, body = self.api.post("/jams", jam, as_user="alex_org")
        self.assertEqual(status, 201)
        self.assertEqual(body["slug"], "fall-jam")

    def test_status_transitions(self):
        self.assertEqual(
            self.api.post("/jams/3/status", {"status": "closed"}, as_user="alex_org")[0], 400
        )
        status, body = self.api.post("/jams/3/status", {"status": "open"}, as_user="alex_org")
        self.assertEqual((status, body["status"]), (200, "open"))

    def test_jam_detail(self):
        status, body = self.api.get("/jams/1")
        self.assertEqual(status, 200)
        self.assertEqual(body["team_count"], 5)
        self.assertEqual(len(body["criteria"]), 3)

    def test_jam_by_slug(self):
        self.assertEqual(self.api.get("/jams/by-slug/spring-mini-jam-2027")[1]["id"], 2)
        self.assertEqual(self.api.get("/jams/by-slug/nope")[0], 404)

    def test_get_team(self):
        status, body = self.api.get("/teams/1")
        self.assertEqual(status, 200)
        self.assertEqual(len(body["members"]), 2)

    def test_unknown_team_returns_not_found(self):
        status, body = self.api.get("/teams/999")
        self.assertEqual(status, 404)
        self.assertEqual(body, {"error": "Team 999 not found"})

    def test_leaderboard_hidden_until_closed(self):
        self.assertEqual(self.api.get("/jams/2/leaderboard")[0], 403)
        self.assertEqual(self.api.get("/jams/2/leaderboard", as_user="alex_org")[0], 200)
        self.assertEqual(self.api.get("/jams/1/leaderboard")[0], 200)

    def test_teams_csv(self):
        self.assertEqual(self.api.get("/jams/1/teams.csv", as_user="sam")[0], 403)
        status, body = self.api.get("/jams/1/teams.csv", as_user="alex_org")
        self.assertEqual(status, 200)
        self.assertTrue(body.startswith("id,name,captain_id"))

    def test_search(self):
        status, body = self.api.get("/search?q=Pixel")
        self.assertEqual(status, 200)
        self.assertEqual(body["teams"][0]["name"], "Pixel Pirates")

    def test_search_needs_term(self):
        self.assertEqual(self.api.get("/search")[0], 400)


if __name__ == "__main__":
    unittest.main()
