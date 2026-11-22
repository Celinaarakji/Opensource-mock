"""Date and time helpers.

All timestamps are stored as ISO 8601 strings. Jams are often created with a
local deadline such as "2026-12-06T23:59:00-05:00" (Toronto time), while the
server records events in UTC. Always go through these helpers when you
compare times so the rules stay in one place.
"""

from datetime import datetime, timedelta, timezone


def now_utc():
    """The current time as an aware UTC datetime."""
    return datetime.now(timezone.utc)


def now_iso():
    """The current UTC time as an ISO 8601 string (seconds precision)."""
    return to_iso(now_utc())


def to_iso(dt):
    """Format a datetime as ISO 8601, without microseconds."""
    return dt.replace(microsecond=0).isoformat()


def parse_datetime(value):
    """Parse an ISO 8601 string into an aware datetime in UTC.

    Accepts a trailing "Z" as well as explicit offsets like "-05:00".
    Strings without any offset are treated as UTC.
    """
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(text)
        except ValueError as exc:
            raise ValueError(f"Not a valid ISO 8601 datetime: {value!r}") from exc
    # Normalise everything to UTC so comparisons are easy.
    return dt.replace(tzinfo=timezone.utc)


def parse_deadline(value):
    """Parse a jam deadline. Kept separate in case deadlines get special rules."""
    return parse_datetime(value)


def is_past_deadline(deadline, at=None):
    """True if `at` (default: now) is after the deadline."""
    moment = parse_datetime(at) if at is not None else now_utc()
    return moment > parse_deadline(deadline)


def time_left(deadline, at=None):
    """A timedelta until the deadline (negative once it has passed)."""
    moment = parse_datetime(at) if at is not None else now_utc()
    return parse_deadline(deadline) - moment


def humanize_delta(delta):
    """Turn a timedelta into short text like '2d 3h' or '45m'."""
    seconds = int(delta.total_seconds())
    sign = "-" if seconds < 0 else ""
    seconds = abs(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes = seconds // 60
    if days:
        return f"{sign}{days}d {hours}h"
    if hours:
        return f"{sign}{hours}h {minutes}m"
    return f"{sign}{minutes}m"


def add_hours(value, hours):
    return to_iso(parse_datetime(value) + timedelta(hours=hours))
