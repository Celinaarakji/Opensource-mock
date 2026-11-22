"""Regression coverage for jam team-size limits."""

import unittest

from gamejam.errors import BadRequest
from gamejam.services import teams
from tests.helpers import ApiClient, SPRING, jam_id, make_conn, team_id, user


class TeamCapacityTests(unittest.TestCase):
    def setUp(self):
        self.conn = make_conn()
        self.addCleanup(self.conn.close)
        self.team_id = team_id(self.conn, "Sprout Squad")
        self.captain = user(self.conn, "sam")

    def test_can_fill_team_to_maximum_but_not_exceed_it(self):
        members = teams.add_member(
            self.conn, self.team_id, user(self.conn, "nora"), self.captain
        )
        self.assertEqual(len(members), 3)
        with self.assertRaisesRegex(BadRequest, "at most 3 members"):
            teams.add_member(
                self.conn, self.team_id, user(self.conn, "zoe"), self.captain
            )
        self.assertEqual(teams.member_count(self.conn, self.team_id), 3)

    def test_api_rejects_member_beyond_limit_without_changing_members(self):
        client = ApiClient(self.conn)
        status, _ = client.post(
            f"/teams/{self.team_id}/members", {"username": "nora"}, as_user="sam"
        )
        self.assertEqual(status, 201)
        status, body = client.post(
            f"/teams/{self.team_id}/members", {"username": "zoe"}, as_user="sam"
        )
        self.assertEqual(status, 400)
        self.assertIn("at most 3 members", str(body))
        self.assertEqual(teams.member_count(self.conn, self.team_id), 3)

    def test_removing_member_frees_capacity(self):
        teams.add_member(self.conn, self.team_id, user(self.conn, "nora"), self.captain)
        teams.remove_member(
            self.conn, self.team_id, user(self.conn, "nora")["id"], self.captain
        )
        members = teams.add_member(
            self.conn, self.team_id, user(self.conn, "zoe"), self.captain
        )
        self.assertEqual(len(members), 3)


if __name__ == "__main__":
    unittest.main()
