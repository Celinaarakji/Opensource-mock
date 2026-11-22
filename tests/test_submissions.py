import unittest

from gamejam.errors import BadRequest, Conflict, Forbidden, NotFound
from gamejam.services import submissions
from tests.helpers import SPRING, WINTER, jam_id, make_conn, team_id, user


class SubmissionTests(unittest.TestCase):
    def setUp(self):
        self.conn = make_conn()
        self.addCleanup(self.conn.close)

    def test_create_submission(self):
        bloom = team_id(self.conn, "Bloom Bots")
        sub = submissions.create_submission(
            self.conn, bloom, {"title": "Petal Pusher"}, user(self.conn, "priya")
        )
        self.assertEqual(sub["title"], "Petal Pusher")
        self.assertEqual(sub["team_name"], "Bloom Bots")
        self.assertIn(sub["is_late"], (True, False))

    def test_one_submission_per_team(self):
        sprout = team_id(self.conn, "Sprout Squad")
        with self.assertRaises(Conflict):
            submissions.create_submission(self.conn, sprout, {"title": "Again"},
                                          user(self.conn, "sam"))

    def test_only_members_submit(self):
        bloom = team_id(self.conn, "Bloom Bots")
        with self.assertRaises(Forbidden):
            submissions.create_submission(self.conn, bloom, {"title": "Not mine"},
                                          user(self.conn, "sam"))

    def test_closed_jam_rejects_submissions(self):
        pirates = team_id(self.conn, "Pixel Pirates")
        conn = self.conn
        conn.execute("DELETE FROM submissions WHERE team_id = ?", (pirates,))
        with self.assertRaises(BadRequest):
            submissions.create_submission(conn, pirates, {"title": "Late"}, user(conn, "sam"))

    def test_update_submission(self):
        sprout = team_id(self.conn, "Sprout Squad")
        existing = submissions.get_submission_for_team(self.conn, sprout)
        updated = submissions.update_submission(
            self.conn, existing["id"], {"description": "Now with music"}, user(self.conn, "leo")
        )
        self.assertEqual(updated["description"], "Now with music")
        self.assertEqual(updated["title"], "Seedling")

    def test_missing_submission(self):
        with self.assertRaises(NotFound):
            submissions.get_submission(self.conn, 9999)

    def test_list_submissions_total(self):
        result = submissions.list_submissions(self.conn, jam_id(self.conn, WINTER), 1, 20)
        self.assertEqual(result["total"], 5)
        self.assertEqual(result["pages"], 1)

    def test_list_late_filter_total(self):
        result = submissions.list_submissions(
            self.conn, jam_id(self.conn, WINTER), 1, 20, late=True
        )
        self.assertEqual(result["total"], 1)

    def test_list_spring(self):
        result = submissions.list_submissions(self.conn, jam_id(self.conn, SPRING), 1, 10)
        self.assertEqual(result["total"], 1)


if __name__ == "__main__":
    unittest.main()
