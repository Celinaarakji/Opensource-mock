"""Text helpers used across services."""

import re
import unicodedata

_SLUG_STRIP = re.compile(r"[^a-z0-9]+")
_SPACES = re.compile(r"\s+")


def slugify(value):
    """'Winter Game Jam 2026!' -> 'winter-game-jam-2026'."""
    text = unicodedata.normalize("NFKD", str(value))
    text = text.encode("ascii", "ignore").decode("ascii").lower()
    return _SLUG_STRIP.sub("-", text).strip("-")


def normalize_name(value):
    """Trim a display name and collapse repeated spaces."""
    return _SPACES.sub(" ", str(value)).strip()


def truncate(value, length=80, suffix="..."):
    text = str(value)
    if len(text) <= length:
        return text
    return text[: length - len(suffix)].rstrip() + suffix


def clamp(value, low, high):
    """Keep a number inside [low, high]."""
    return max(low, min(high, value))


def is_blank(value):
    return value is None or str(value).strip() == ""
