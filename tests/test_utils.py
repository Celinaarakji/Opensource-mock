import unittest
from datetime import timedelta

from gamejam.errors import BadRequest
from gamejam.utils.formatting import round_score, to_csv
from gamejam.utils.pagination import get_page_params, paginate
from gamejam.utils.text import clamp, is_blank, normalize_name, slugify, truncate
from gamejam.utils.time import humanize_delta, parse_datetime


class TextTests(unittest.TestCase):
    def test_slugify(self):
        self.assertEqual(slugify("Winter Game Jam 2026!"), "winter-game-jam-2026")
        self.assertEqual(slugify("  Café  Jam "), "cafe-jam")
        self.assertEqual(slugify("!!!"), "")

    def test_normalize_name(self):
        self.assertEqual(normalize_name("  Pixel    Pirates "), "Pixel Pirates")

    def test_truncate(self):
        self.assertEqual(truncate("short"), "short")
        self.assertEqual(truncate("a" * 100, length=10), "aaaaaaa...")

    def test_clamp(self):
        self.assertEqual(clamp(5, 1, 10), 5)
        self.assertEqual(clamp(-3, 1, 10), 1)
        self.assertEqual(clamp(42, 1, 10), 10)

    def test_is_blank(self):
        self.assertTrue(is_blank(None))
        self.assertTrue(is_blank("   "))
        self.assertFalse(is_blank("x"))


class TimeTests(unittest.TestCase):
    def test_parse_z_suffix(self):
        dt = parse_datetime("2026-12-07T02:30:00Z")
        self.assertEqual((dt.year, dt.month, dt.day, dt.hour), (2026, 12, 7, 2))

    def test_parse_invalid(self):
        with self.assertRaises(ValueError):
            parse_datetime("next tuesday")

    def test_humanize_delta(self):
        self.assertEqual(humanize_delta(timedelta(days=2, hours=3)), "2d 3h")
        self.assertEqual(humanize_delta(timedelta(hours=1, minutes=5)), "1h 5m")
        self.assertEqual(humanize_delta(timedelta(minutes=-45)), "-45m")


class PaginationTests(unittest.TestCase):
    def test_defaults(self):
        self.assertEqual(get_page_params({}), (1, 20))

    def test_limit_is_capped(self):
        self.assertEqual(get_page_params({"page": "2", "limit": "500"}), (2, 100))

    def test_bad_values(self):
        with self.assertRaises(BadRequest):
            get_page_params({"page": "abc"})
        with self.assertRaises(BadRequest):
            get_page_params({"page": "0"})

    def test_paginate_shape(self):
        result = paginate([1, 2], page=1, limit=2, total=5)
        self.assertEqual(result["pages"], 3)
        self.assertEqual(result["total"], 5)


class FormattingTests(unittest.TestCase):
    def test_to_csv(self):
        text = to_csv([{"id": 1, "name": "A", "extra": "x"}], ["id", "name"])
        self.assertEqual(text.splitlines(), ["id,name", "1,A"])

    def test_round_score(self):
        self.assertEqual(round_score(7.456), 7.46)
        self.assertIsNone(round_score(None))


if __name__ == "__main__":
    unittest.main()
