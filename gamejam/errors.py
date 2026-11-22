"""Errors that turn into JSON error responses.

Raise one of these anywhere in a service or route and the server will send
`{"error": "<message>"}` with the matching status code.
"""


class ApiError(Exception):
    status = 500

    def __init__(self, message="Something went wrong", details=None):
        super().__init__(message)
        self.message = message
        self.details = details

    def to_dict(self):
        body = {"error": self.message}
        if self.details:
            body["details"] = self.details
        return body


class BadRequest(ApiError):
    status = 400


class Unauthorized(ApiError):
    status = 401


class Forbidden(ApiError):
    status = 403


class NotFound(ApiError):
    status = 404


class Conflict(ApiError):
    status = 409


class ValidationError(BadRequest):
    """A request body failed validation. `details` maps field -> problem."""

    def __init__(self, details):
        super().__init__("Validation failed", details)
