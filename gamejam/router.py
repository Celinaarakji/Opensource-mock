"""A tiny URL router.

Routes are registered with a decorator:

    @router.route("GET", "/jams/{jam_id:int}")
    def get_jam(req):
        ...

`{name}` matches one path segment as a string and `{name:int}` as an int.
The values end up in `req.params`.
"""

import re

from gamejam.errors import ApiError, NotFound

_PARAM = re.compile(r"\{(\w+)(?::(int|str))?\}")


class MethodNotAllowed(ApiError):
    status = 405


class Route:
    def __init__(self, method, pattern, handler, auth=True):
        self.method = method.upper()
        self.pattern = pattern
        self.handler = handler
        self.auth = auth
        self.converters = {}
        self.regex = self._compile(pattern)

    def _compile(self, pattern):
        regex = "^"
        last = 0
        for match in _PARAM.finditer(pattern):
            regex += re.escape(pattern[last:match.start()])
            name, kind = match.group(1), match.group(2) or "str"
            if kind == "int":
                regex += rf"(?P<{name}>\d+)"
                self.converters[name] = int
            else:
                regex += rf"(?P<{name}>[^/]+)"
                self.converters[name] = str
            last = match.end()
        regex += re.escape(pattern[last:]) + "$"
        return re.compile(regex)

    def match(self, path):
        m = self.regex.match(path)
        if not m:
            return None
        return {k: self.converters[k](v) for k, v in m.groupdict().items()}


class Router:
    def __init__(self):
        self.routes = []

    def route(self, method, pattern, auth=True):
        """Decorator that registers a handler. Set auth=False for public routes."""

        def decorator(handler):
            self.routes.append(Route(method, pattern, handler, auth=auth))
            return handler

        return decorator

    def resolve(self, method, path):
        """Find the route for a request. Returns (route, params)."""
        path = path.rstrip("/") or "/"
        allowed = []
        for route in self.routes:
            params = route.match(path)
            if params is None:
                continue
            if route.method == method.upper():
                return route, params
            allowed.append(route.method)
        if allowed:
            raise MethodNotAllowed(f"Use one of: {', '.join(sorted(set(allowed)))}")
        raise NotFound(f"No route for {method} {path}")

    def describe(self):
        """List all routes, used by GET / to document the API."""
        return [
            {"method": r.method, "path": r.pattern, "auth": r.auth}
            for r in sorted(self.routes, key=lambda r: (r.pattern, r.method))
        ]
