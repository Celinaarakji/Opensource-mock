"""Request and response objects plus the HTTP server glue.

Route handlers receive a `Request` and return either:
  * a dict or list  -> sent as JSON with status 200
  * (status, body)  -> sent as JSON with that status
  * a `Response`    -> sent as-is (used for CSV downloads)
"""

import json
import logging
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from gamejam import auth
from gamejam.errors import ApiError, BadRequest

log = logging.getLogger("gamejam")

MAX_BODY_BYTES = 1_000_000


class Request:
    def __init__(self, method, path, query, headers, raw_body, conn):
        self.method = method
        self.path = path
        self.query = query
        self.headers = headers
        self.raw_body = raw_body
        self.conn = conn
        self.params = {}
        self.user = None
        self._json = None

    @property
    def json(self):
        """The request body parsed as JSON (an empty dict if there is none)."""
        if self._json is None:
            if not self.raw_body:
                self._json = {}
            else:
                try:
                    self._json = json.loads(self.raw_body.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    raise BadRequest("Request body must be valid JSON")
        return self._json


class Response:
    def __init__(self, body, status=200, content_type="application/json", headers=None):
        self.body = body
        self.status = status
        self.content_type = content_type
        self.headers = headers or {}

    def encode(self):
        if isinstance(self.body, (bytes, bytearray)):
            return bytes(self.body)
        if self.content_type == "application/json":
            return json.dumps(self.body, indent=2, default=str).encode("utf-8")
        return str(self.body).encode("utf-8")


def to_response(result):
    if isinstance(result, Response):
        return result
    if isinstance(result, tuple):
        status, body = result
        return Response(body, status=status)
    if result is None:
        return Response(b"", status=204)
    return Response(result)


def dispatch(router, conn, method, target, headers, raw_body):
    """Run one request through the router. Used by the server and by tests."""
    parsed = urlparse(target)
    query = {k: v[-1] for k, v in parse_qs(parsed.query).items()}
    req = Request(method, parsed.path, query, headers, raw_body, conn)
    try:
        route, params = router.resolve(method, parsed.path)
        req.params = params
        req.user = auth.user_from_header(conn, headers.get("Authorization"))
        if route.auth:
            auth.require_user(req.user)
        return to_response(route.handler(req))
    except ApiError as err:
        return Response(err.to_dict(), status=err.status)
    except Exception:  # noqa: BLE001 - last line of defence
        log.error("Unhandled error on %s %s\n%s", method, target, traceback.format_exc())
        return Response({"error": "Internal server error"}, status=500)


def make_handler(router, conn):
    class Handler(BaseHTTPRequestHandler):
        server_version = "GameJamAPI/0.3"

        def _handle(self):
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_BODY_BYTES:
                response = Response({"error": "Request body too large"}, status=413)
            else:
                raw = self.rfile.read(length) if length else b""
                response = dispatch(router, conn, self.command, self.path, self.headers, raw)
            payload = response.encode()
            self.send_response(response.status)
            self.send_header("Content-Type", f"{response.content_type}; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            for key, value in response.headers.items():
                self.send_header(key, value)
            self.end_headers()
            if payload:
                self.wfile.write(payload)

        do_GET = do_POST = do_PUT = do_PATCH = do_DELETE = _handle

        def log_message(self, fmt, *args):
            log.info("%s - %s", self.address_string(), fmt % args)

    return Handler


def serve(router, conn, host, port):
    server = ThreadingHTTPServer((host, port), make_handler(router, conn))
    log.info("Game Jam API running on http://%s:%s", host, port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Shutting down")
    finally:
        server.server_close()
