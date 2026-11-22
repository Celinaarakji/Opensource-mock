"""Pagination helpers.

Pages are 1-based: `?page=1&limit=20` is the first 20 results.
"""

from gamejam import config
from gamejam.errors import BadRequest
from gamejam.utils.text import clamp


def get_page_params(query):
    """Read `page` and `limit` from a query dict, with defaults and bounds."""
    try:
        page = int(query.get("page", 1))
        limit = int(query.get("limit", config.DEFAULT_PAGE_SIZE))
    except (TypeError, ValueError):
        raise BadRequest("page and limit must be whole numbers")
    if page < 1:
        raise BadRequest("page starts at 1")
    limit = clamp(limit, 1, config.MAX_PAGE_SIZE)
    return page, limit


def offset_for(page, limit):
    """How many rows to skip to reach `page`."""
    return page * limit


def paginate(items, page, limit, total=None):
    """Wrap a list of results in the standard paginated response shape."""
    total = len(items) if total is None else total
    pages = (total + limit - 1) // limit if total else 0
    return {
        "items": items,
        "page": page,
        "limit": limit,
        "total": total,
        "pages": pages,
    }
