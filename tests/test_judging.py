import unittest

from gamejam.errors import BadRequest, Forbidden
from gamejam.services import jams, judging, submissions
from tests.helpers import SPRING, jam_id, make_conn, team_id, user


class JudgingTests(unittest.TestCase):
    def setUp(self):
        self.conn = make_conn()
        self.addCleanup(self.conn.close)
        self.spring = jam_id(self.conn, SPRING)
        jams.set_status(self.conn, self.spring, "judging")
        sprout = team_id(self.conn, "Sprout Squad")
        self.submission = submissions.get_submission_for_team(self.conn, sprout)
        self.criteria = [c["id"] for c in jams.list_criteria(self.conn, self.spring)]

    def body(self, value=8):
        return {"scores": [{"criterion_id": cid, "value": value} for cid in self.criteria]}

    def test_judge_scores_submission(self):
        result = judging.submit_scores(self.conn, self.submission["id"], self.body(),
                                       user(self.conn, "maya_judge"))
        self.assertEqual([r["value"] for r in result], [8, 8])

    def test_unassigned_judge_rejected(self):
        with self.assertRaises(Forbidden):
            judging.submit_scores(self.conn, self.submission["id"], self.body(),
                                  user(self.conn, "omar_judge"))

    def test_participant_rejected(self):
        with self.assertRaises(Forbidden):
            judging.submit_scores(self.conn, self.submission["id"], self.body(),
                                  user(self.conn, "priya"))

    def test_only_while_judging(self):
        jams.set_status(self.conn, self.spring, "open")
        with self.assertRaises(BadRequest):
            judging.submit_scores(self.conn, self.submission["id"], self.body(),
                                  user(self.conn, "maya_judge"))

    def test_criterion_from_other_jam(self):
        body = {"scores": [{"criterion_id": 1, "value": 5}]}  # criterion 1 is a winter one
        with self.assertRaises(BadRequest):
            judging.submit_scores(self.conn, self.submission["id"], body,
                                  user(self.conn, "maya_judge"))

    def test_captain_cannot_judge_own_team(self):
        maya = user(self.conn, "maya_judge")
        self.conn.execute("UPDATE teams SET captain_id = ? WHERE id = ?",
                          (maya["id"], self.submission["team_id"]))
        with self.assertRaises(Forbidden):
            judging.submit_scores(self.conn, self.submission["id"], self.body(), maya)

    def test_progress(self):
        maya = user(self.conn, "maya_judge")
        before = judging.judge_progress(self.conn, self.spring, maya["id"])
        self.assertEqual((before["done"], before["total"]), (0, 1))
        judging.submit_scores(self.conn, self.submission["id"], self.body(), maya)
        after = judging.judge_progress(self.conn, self.spring, maya["id"])
        self.assertEqual(after["done"], 1)


if __name__ == "__main__":
    unittest.main()
