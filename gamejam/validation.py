"""Request body validation.

Each `validate_*` function takes the parsed JSON body and either returns a
clean dict of values or raises `ValidationError` listing every problem.
"""

import re
from urllib.parse import urlparse

from gamejam import config
from gamejam.errors import ValidationError
from gamejam.utils.text import is_blank, normalize_name
from gamejam.utils.time import parse_datetime

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
USERNAME_RE = re.compile(r"^[a-zA-Z0-9_-]{3,30}$")


class Checker:
    """Collects field errors so we can report them all at once."""

    def __init__(self, body):
        if not isinstance(body, dict):
            raise ValidationError({"body": "must be a JSON object"})
        self.body = body
        self.errors = {}
        self.clean = {}

    def required_text(self, field, max_length=200):
        value = self.body.get(field)
        if is_blank(value):
            self.errors[field] = "is required"
            return
        value = normalize_name(value)
        if len(value) > max_length:
            self.errors[field] = f"must be at most {max_length} characters"
            return
        self.clean[field] = value

    def optional_text(self, field, max_length=2000):
        value = self.body.get(field)
        if is_blank(value):
            return
        value = str(value).strip()
        if len(value) > max_length:
            self.errors[field] = f"must be at most {max_length} characters"
            return
        self.clean[field] = value

    def optional_url(self, field):
        value = self.body.get(field)
        if is_blank(value):
            return
        parsed = urlparse(str(value))
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            self.errors[field] = "must be an http(s) URL"
            return
        self.clean[field] = str(value)

    def datetime_field(self, field, required=True):
        value = self.body.get(field)
        if is_blank(value):
            if required:
                self.errors[field] = "is required"
            return
        try:
            parse_datetime(value)
        except ValueError:
            self.errors[field] = "must be an ISO 8601 datetime"
            return
        self.clean[field] = str(value)

    def positive_int(self, field, required=True, default=None):
        value = self.body.get(field, default)
        if value is None:
            if required:
                self.errors[field] = "is required"
            return
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            self.errors[field] = "must be a positive whole number"
            return
        self.clean[field] = value

    def done(self):
        if self.errors:
            raise ValidationError(self.errors)
        return self.clean


def validate_user(body):
    c = Checker(body)
    username = body.get("username") if isinstance(body, dict) else None
    if not username or not USERNAME_RE.match(str(username)):
        c.errors["username"] = "3-30 letters, numbers, _ or -"
    else:
        c.clean["username"] = username
    c.required_text("display_name", max_length=60)
    email = body.get("email")
    if not email or not EMAIL_RE.match(str(email)):
        c.errors["email"] = "must be a valid email address"
    else:
        c.clean["email"] = str(email).lower()
    role = body.get("role", config.ROLE_PARTICIPANT)
    if role not in config.ROLES:
        c.errors["role"] = f"must be one of {', '.join(config.ROLES)}"
    else:
        c.clean["role"] = role
    return c.done()


def validate_jam(body):
    c = Checker(body)
    c.required_text("name", max_length=80)
    c.optional_text("theme", max_length=200)
    c.datetime_field("starts_at")
    c.datetime_field("deadline")
    c.positive_int("max_team_size", required=False, default=config.DEFAULT_MAX_TEAM_SIZE)
    clean = c.done()
    if parse_datetime(clean["deadline"]) <= parse_datetime(clean["starts_at"]):
        raise ValidationError({"deadline": "must be after starts_at"})
    return clean


def validate_team(body):
    c = Checker(body)
    c.required_text("name", max_length=50)
    return c.done()


def validate_submission(body, partial=False):
    c = Checker(body)
    if partial:
        c.optional_text("title", max_length=100)
    else:
        c.required_text("title", max_length=100)
    c.optional_text("description")
    c.optional_url("repo_url")
    c.optional_url("demo_url")
    return c.done()


def validate_criterion(body):
    c = Checker(body)
    c.required_text("name", max_length=50)
    weight = body.get("weight", 1.0)
    if not isinstance(weight, (int, float)) or isinstance(weight, bool) or weight <= 0:
        c.errors["weight"] = "must be a positive number"
    else:
        c.clean["weight"] = float(weight)
    return c.done()


def validate_score_value(value):
    """True if `value` is an allowed score (whole number from MIN to MAX)."""
    if not isinstance(value, int) or isinstance(value, bool):
        return False
    return value in range(config.MIN_SCORE, config.MAX_SCORE)


def validate_scores(body):
    """Body: {"scores": [{"criterion_id": 1, "value": 8}, ...], "comment": "..."}"""
    c = Checker(body)
    entries = body.get("scores")
    if not isinstance(entries, list) or not entries:
        raise ValidationError({"scores": "must be a non-empty list"})
    clean_entries = []
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            c.errors[f"scores[{i}]"] = "must be an object"
            continue
        criterion_id = entry.get("criterion_id")
        value = entry.get("value")
        if not isinstance(criterion_id, int):
            c.errors[f"scores[{i}].criterion_id"] = "is required"
        if not validate_score_value(value):
            c.errors[f"scores[{i}].value"] = (
                f"must be a whole number from {config.MIN_SCORE} to {config.MAX_SCORE}"
            )
        clean_entries.append({"criterion_id": criterion_id, "value": value})
    c.optional_text("comment", max_length=1000)
    clean = c.done()
    clean["scores"] = clean_entries
    return clean
