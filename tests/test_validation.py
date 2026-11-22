import unittest

from gamejam.errors import ValidationError
from gamejam.validation import (
    validate_criterion,
    validate_jam,
    validate_score_value,
    validate_scores,
    validate_submission,
    validate_team,
    validate_user,
)


class UserValidationTests(unittest.TestCase):
    def test_valid_user(self):
        data = validate_user(
            {"username": "new_dev", "display_name": " New  Dev ", "email": "NEW@Example.com"}
        )
        self.assertEqual(data["display_name"], "New Dev")
        self.assertEqual(data["email"], "new@example.com")
        self.assertEqual(data["role"], "participant")

    def test_reports_every_problem(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_user({"username": "x", "email": "nope", "role": "admin"})
        self.assertEqual(
            set(ctx.exception.details), {"username", "display_name", "email", "role"}
        )


class JamValidationTests(unittest.TestCase):
    def test_deadline_after_start(self):
        with self.assertRaises(ValidationError):
            validate_jam(
                {
                    "name": "Backwards Jam",
                    "starts_at": "2027-01-02T00:00:00Z",
                    "deadline": "2027-01-01T00:00:00Z",
                }
            )

    def test_default_team_size(self):
        data = validate_jam(
            {
                "name": "Jam",
                "starts_at": "2027-01-01T00:00:00Z",
                "deadline": "2027-01-03T00:00:00Z",
            }
        )
        self.assertEqual(data["max_team_size"], 4)


class OtherValidationTests(unittest.TestCase):
    def test_team_name_required(self):
        with self.assertRaises(ValidationError):
            validate_team({"name": "   "})

    def test_submission_urls(self):
        with self.assertRaises(ValidationError):
            validate_submission({"title": "Game", "repo_url": "ftp://example.com"})
        data = validate_submission({"title": "Game", "repo_url": "https://github.com/a/b"})
        self.assertEqual(data["repo_url"], "https://github.com/a/b")

    def test_partial_submission(self):
        self.assertEqual(validate_submission({}, partial=True), {})

    def test_criterion_weight(self):
        with self.assertRaises(ValidationError):
            validate_criterion({"name": "Fun", "weight": 0})
        self.assertEqual(validate_criterion({"name": "Fun"})["weight"], 1.0)


class ScoreValidationTests(unittest.TestCase):
    def test_score_values(self):
        self.assertTrue(validate_score_value(1))
        self.assertTrue(validate_score_value(7))
        self.assertFalse(validate_score_value(0))
        self.assertFalse(validate_score_value(11))
        self.assertFalse(validate_score_value(7.5))
        self.assertFalse(validate_score_value(True))

    def test_scores_body(self):
        data = validate_scores({"scores": [{"criterion_id": 1, "value": 8}], "comment": "Nice"})
        self.assertEqual(data["scores"], [{"criterion_id": 1, "value": 8}])
        self.assertEqual(data["comment"], "Nice")

    def test_empty_scores(self):
        with self.assertRaises(ValidationError):
            validate_scores({"scores": []})


if __name__ == "__main__":
    unittest.main()
