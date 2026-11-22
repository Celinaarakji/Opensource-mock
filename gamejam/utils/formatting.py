"""Output formatting helpers (CSV, numbers)."""

import csv
import io


def to_csv(rows, columns):
    """Render a list of dicts as CSV text with the given column order."""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue()


def round_score(value, places=2):
    """Round a score for display. Returns None for missing scores."""
    if value is None:
        return None
    return round(float(value), places)
