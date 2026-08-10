from __future__ import annotations

import secrets

from fastapi import Request, Response

SESSION_COOKIE = "eav_session"
TOKEN_BYTES = 32
MIN_TOKEN_LENGTH = 16
MAX_TOKEN_LENGTH = 128


def _acceptable(token: str) -> bool:
    return MIN_TOKEN_LENGTH <= len(token) <= MAX_TOKEN_LENGTH


def get_session_token(request: Request, response: Response) -> str:
    """Return the caller's opaque session token, minting one when needed.

    The token does not identify a person and is not authentication. It only
    partitions stored runs so one browser session cannot list or fetch
    another session's uploads. Endpoints that return a bare ``Response``
    (the report downloads) do not propagate the ``Set-Cookie`` header, which
    is fine: by the time a report URL exists, the creating request has
    already set the cookie, and a caller without the right token gets 404.
    """
    token = request.cookies.get(SESSION_COOKIE, "")
    if not _acceptable(token):
        token = secrets.token_urlsafe(TOKEN_BYTES)
        response.set_cookie(
            SESSION_COOKIE,
            token,
            httponly=True,
            samesite="lax",
        )
    return token
