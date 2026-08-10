"""Optional bearer-token authentication with per-token run isolation.

When ``EAV_API_TOKENS`` is empty the API stays open and stored runs are
scoped to the ``eav_session`` cookie exactly as before. When one or more
tokens are configured, every data route demands one of them, and the token
replaces the cookie as the scope key: runs created with one token are
invisible to every other token, with the same 404 discipline the session
scoping established. The cookie is neither read nor set in that mode - a
shared team token, not a browser, owns the runs.
"""

from __future__ import annotations

import hashlib
import secrets

from fastapi import HTTPException, Request, Response

from .config import Settings
from .session import get_session_token

# Session cookies never contain a colon (session.py rejects them), so this
# prefix keeps hashed-token scope keys disjoint from cookie scope keys even
# if a deployment later toggles authentication on or off.
TOKEN_SCOPE_PREFIX = "token:"  # noqa: S105 -- namespace marker, not a credential


def token_scope_key(token: str) -> str:
    """Return the scope key stored on runs created with ``token``.

    Only the SHA-256 of the token lands in the database: the token is a
    credential, and a database dump or backup must not leak something that
    can be replayed against the API.
    """
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return f"{TOKEN_SCOPE_PREFIX}{digest}"


def _bearer_credentials(request: Request) -> str | None:
    header = request.headers.get("Authorization")
    if header is None:
        return None
    scheme, _, credentials = header.partition(" ")
    if scheme.lower() != "bearer":
        return None
    return credentials.strip() or None


def _matches_configured(candidate: str, configured: list[str]) -> bool:
    # Bytes keep compare_digest from raising on non-ASCII input, and
    # compare_digest keeps each comparison constant-time so response timing
    # does not reveal how much of a guessed token was correct. Every
    # configured token is checked even after a match so timing does not
    # reveal which position matched either.
    candidate_bytes = candidate.encode("utf-8")
    matched = False
    for token in configured:
        if secrets.compare_digest(candidate_bytes, token.encode("utf-8")):
            matched = True
    return matched


def _authenticate(request: Request, settings: Settings) -> str:
    candidate = _bearer_credentials(request)
    if candidate is None or not _matches_configured(candidate, settings.api_tokens):
        raise HTTPException(
            status_code=401,
            detail="A valid bearer token is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return candidate


def require_token(request: Request) -> None:
    """Dependency for routes that need authentication but store nothing.

    ``/inspections`` processes uploads without persisting a run, so it has
    no scope key; it still must not serve anonymous callers when the
    deployment requires tokens.
    """
    settings: Settings = request.app.state.settings
    if settings.api_tokens:
        _authenticate(request, settings)


def get_scope_key(request: Request, response: Response) -> str:
    """Return the key that scopes stored runs for this request.

    Token deployments get the hashed token; open deployments fall through
    to the session cookie unchanged, including minting it when absent.
    """
    settings: Settings = request.app.state.settings
    if not settings.api_tokens:
        return get_session_token(request, response)
    return token_scope_key(_authenticate(request, settings))
