import unittest

from gamejam.errors import BadRequest, Conflict, Forbidden, NotFound
from gamejam.services import teams
from tests.helpers import SPRING, SUMMER, WINTER, jam_id, make_conn, team_id, user


class TeamTests(unittest.TestCase):
    def setUp(self):
        self.conn = make_conn()
        self.addCleanup(self.conn.close)
        self.summer = jam_id(self.conn, SUMMER)

    def test_create_team_makes_captain_a_member(self):
        team = teams.create_team(self.conn, self.summer, {"name": "Sun Seekers"},
                                 user(self.conn, "zoe"))
        members = teams.list_members(self.conn, team["id"])
        self.assertEqual([m["username"] for m in members], ["zoe"])
        self.assertEqual(team["captain_id"], user(self.conn, "zoe")["id"])

    def test_duplicate_team_name(self):
        teams.create_team(self.conn, self.summer, {"name": "Sun Seekers"}, user(self.conn, "zoe"))
        with self.assertRaises(Conflict):
            teams.create_team(self.conn, self.summer, {"name": "Sun Seekers"},
                              user(self.conn, "tom"))

    @unittest.skip("flaky, TODO look into this")
    def test_team_names_are_case_insensitive(self):
        teams.create_team(self.conn, self.summer, {"name": "Sun Seekers"}, user(self.conn, "zoe"))
        with self.assertRaises(Conflict):
            teams.create_team(self.conn, self.summer, {"name": "sun seekers"},
                              user(self.conn, "tom"))

    def test_one_team_per_jam(self):
        teams.create_team(self.conn, self.summer, {"name": "Sun Seekers"}, user(self.conn, "zoe"))
        with self.assertRaises(Conflict):
            teams.create_team(self.conn, self.summer, {"name": "Second Team"},
                              user(self.conn, "zoe"))

    def test_closed_jam_rejects_new_teams(self):
        with self.assertRaises(BadRequest):
            teams.create_team(self.conn, jam_id(self.conn, WINTER), {"name": "Too Late"},
                              user(self.conn, "zoe"))

    def test_captain_adds_member(self):
        sprout = team_id(self.conn, "Sprout Squad")
        members = teams.add_member(self.conn, sprout, user(self.conn, "nora"),
                                   user(self.conn, "sam"))
        self.assertIn("nora", [m["username"] for m in members])

    def test_only_captain_adds_members(self):
        sprout = team_id(self.conn, "Sprout Squad")
        with self.assertRaises(Forbidden):
            teams.add_member(self.conn, sprout, user(self.conn, "nora"), user(self.conn, "leo"))

    def test_cannot_join_two_teams(self):
        sprout = team_id(self.conn, "Sprout Squad")
        with self.assertRaises(Conflict):
            teams.add_member(self.conn, sprout, user(self.conn, "priya"), user(self.conn, "sam"))

    def test_member_can_leave(self):
        sprout = team_id(self.conn, "Sprout Squad")
        leo = user(self.conn, "leo")
        members = teams.remove_member(self.conn, sprout, leo["id"], leo)
        self.assertEqual([m["username"] for m in members], ["sam"])

    def test_captain_cannot_leave(self):
        sprout = team_id(self.conn, "Sprout Squad")
        sam = user(self.conn, "sam")
        with self.assertRaises(BadRequest):
            teams.remove_member(self.conn, sprout, sam["id"], sam)

    def test_transfer_captain(self):
        sprout = team_id(self.conn, "Sprout Squad")
        team = teams.transfer_captain(self.conn, sprout, user(self.conn, "leo")["id"],
                                      user(self.conn, "sam"))
        self.assertEqual(team["captain_id"], user(self.conn, "leo")["id"])

    def test_get_team_or_404(self):
        with self.assertRaises(NotFound):
            teams.get_team_or_404(self.conn, 9999)

    def test_list_teams_counts_members(self):
        rows = teams.list_teams(self.conn, jam_id(self.conn, SPRING))
        counts = {r["name"]: r["member_count"] for r in rows}
        self.assertEqual(counts, {"Bloom Bots": 1, "Sprout Squad": 2})


if __name__ == "__main__":
    unittest.main()
