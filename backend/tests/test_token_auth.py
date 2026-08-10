from __future__ import annotations

import hashlib
import secrets
import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from electrical_asset_validator.config import Settings
from electrical_asset_validator.main import create_app

pytestmark = pytest.mark.anyio

TOKEN_ALPHA = "alpha-team-shared-token"  # noqa: S105 -- fictional test credential
TOKEN_BETA = "beta-team-shared-token"  # noqa: S105 -- fictional test credential


def _files(content: bytes, filename: str = "assets.csv") -> dict[str, Any]:
    return {"file": (filename, content, "text/csv")}


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@asynccontextmanager
async def _app_clients(
    tmp_path: Path,
    api_tokens: list[str] | None = None,
) -> AsyncIterator[tuple[AsyncClient, AsyncClient, str]]:
    """One application and two clients with independent cookie jars.

    Returns the SQLite database path as well so tests can inspect what
    actually got stored.
    """
    database_path = (tmp_path / "auth.db").as_posix()
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        docs_enabled=False,
        max_upload_mb=1,
        api_tokens=api_tokens or [],
    )
    application = create_app(settings)
    transport = ASGITransport(app=application)
    async with application.router.lifespan_context(application):
        async with (
            AsyncClient(transport=transport, base_url="http://testserver") as first,
            AsyncClient(transport=transport, base_url="http://testserver") as second,
        ):
            yield first, second, database_path


async def test_config_endpoint_reports_auth_disabled_by_default(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/v1/config")

    assert response.status_code == 200
    assert response.json() == {"auth_required": False}


async def test_config_and_health_stay_open_when_auth_is_enabled(tmp_path: Path) -> None:
    async with _app_clients(tmp_path, [TOKEN_ALPHA]) as (anonymous, _, _):
        config = await anonymous.get("/api/v1/config")
        assert config.status_code == 200
        assert config.json() == {"auth_required": True}

        health = await anonymous.get("/api/v1/health")
        assert health.status_code == 200


async def test_requests_without_a_token_are_rejected(tmp_path: Path, clean_csv: bytes) -> None:
    async with _app_clients(tmp_path, [TOKEN_ALPHA]) as (anonymous, _, _):
        listing = await anonymous.get("/api/v1/validations")
        assert listing.status_code == 401
        assert listing.headers["WWW-Authenticate"] == "Bearer"

        created = await anonymous.post("/api/v1/validations", files=_files(clean_csv))
        assert created.status_code == 401

        inspected = await anonymous.post("/api/v1/inspections", files=_files(clean_csv))
        assert inspected.status_code == 401

        compared = await anonymous.post(
            "/api/v1/comparisons",
            files={
                "before_file": ("before.csv", clean_csv, "text/csv"),
                "after_file": ("after.csv", clean_csv, "text/csv"),
            },
        )
        assert compared.status_code == 401

        # Authentication is checked before any lookup, so an unauthenticated
        # probe cannot distinguish existing ids from missing ones.
        probe = await anonymous.get("/api/v1/validations/any-id")
        assert probe.status_code == 401


async def test_wrong_or_malformed_credentials_are_rejected(tmp_path: Path) -> None:
    async with _app_clients(tmp_path, [TOKEN_ALPHA]) as (anonymous, _, _):
        for headers in (
            _bearer("not-the-configured-token"),
            _bearer(""),
            {"Authorization": "Bearer"},
            {"Authorization": f"Basic {TOKEN_ALPHA}"},
            {"Authorization": TOKEN_ALPHA},
        ):
            response = await anonymous.get("/api/v1/validations", headers=headers)
            assert response.status_code == 401, headers
            assert response.headers["WWW-Authenticate"] == "Bearer"


async def test_any_configured_token_is_accepted_and_no_cookie_is_set(
    tmp_path: Path, clean_csv: bytes
) -> None:
    async with _app_clients(tmp_path, [TOKEN_ALPHA, TOKEN_BETA]) as (alice, bob, _):
        created = await alice.post(
            "/api/v1/validations",
            files=_files(clean_csv),
            headers=_bearer(TOKEN_ALPHA),
        )
        assert created.status_code == 201
        # The token replaces the session cookie as the scope key, so no
        # cookie is minted on authenticated deployments.
        assert "set-cookie" not in created.headers

        other = await bob.get("/api/v1/validations", headers=_bearer(TOKEN_BETA))
        assert other.status_code == 200

        inspected = await alice.post(
            "/api/v1/inspections",
            files=_files(clean_csv),
            headers=_bearer(TOKEN_ALPHA),
        )
        assert inspected.status_code == 200


async def test_tokens_cannot_see_each_others_runs(tmp_path: Path, clean_csv: bytes) -> None:
    async with _app_clients(tmp_path, [TOKEN_ALPHA, TOKEN_BETA]) as (alice, bob, _):
        validation = await alice.post(
            "/api/v1/validations",
            files=_files(clean_csv),
            headers=_bearer(TOKEN_ALPHA),
        )
        comparison = await alice.post(
            "/api/v1/comparisons",
            files={
                "before_file": ("before.csv", clean_csv, "text/csv"),
                "after_file": ("after.csv", clean_csv, "text/csv"),
            },
            headers=_bearer(TOKEN_ALPHA),
        )
        assert validation.status_code == 201
        assert comparison.status_code == 201
        validation_id = validation.json()["id"]
        comparison_id = comparison.json()["id"]

        own_history = await alice.get("/api/v1/validations", headers=_bearer(TOKEN_ALPHA))
        assert [item["id"] for item in own_history.json()] == [validation_id]
        assert (
            await alice.get(
                f"/api/v1/validations/{validation_id}",
                headers=_bearer(TOKEN_ALPHA),
            )
        ).status_code == 200

        foreign_history = await bob.get("/api/v1/validations", headers=_bearer(TOKEN_BETA))
        assert foreign_history.status_code == 200
        assert foreign_history.json() == []

        for path in (
            f"/api/v1/validations/{validation_id}",
            f"/api/v1/validations/{validation_id}/report.xlsx",
            f"/api/v1/validations/{validation_id}/report.pdf",
            f"/api/v1/comparisons/{comparison_id}",
        ):
            foreign = await bob.get(path, headers=_bearer(TOKEN_BETA))
            assert foreign.status_code == 404, path


async def test_session_cookies_grant_nothing_when_auth_is_on(
    tmp_path: Path, clean_csv: bytes
) -> None:
    async with _app_clients(tmp_path, [TOKEN_ALPHA]) as (alice, _, _):
        alice.cookies.set("eav_session", "cookie-from-an-open-deployment")
        created = await alice.post("/api/v1/validations", files=_files(clean_csv))
        assert created.status_code == 401

        listing = await alice.get("/api/v1/validations")
        assert listing.status_code == 401


async def test_stored_scope_key_is_a_hash_not_the_raw_token(
    tmp_path: Path, clean_csv: bytes
) -> None:
    async with _app_clients(tmp_path, [TOKEN_ALPHA]) as (alice, _, database_path):
        created = await alice.post(
            "/api/v1/validations",
            files=_files(clean_csv),
            headers=_bearer(TOKEN_ALPHA),
        )
        assert created.status_code == 201

        connection = sqlite3.connect(database_path)
        try:
            rows = connection.execute("SELECT session_token FROM validation_runs").fetchall()
        finally:
            connection.close()

        expected = "token:" + hashlib.sha256(TOKEN_ALPHA.encode("utf-8")).hexdigest()
        assert [value for (value,) in rows] == [expected]
        assert all(TOKEN_ALPHA not in value for (value,) in rows)


async def test_token_comparison_goes_through_compare_digest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pin the constant-time comparison mechanism, not its timing."""
    calls: list[tuple[bytes, bytes]] = []
    real_compare_digest = secrets.compare_digest

    def recording_compare_digest(left: bytes, right: bytes) -> bool:
        calls.append((left, right))
        return real_compare_digest(left, right)

    # auth.py resolves secrets.compare_digest at call time, so patching the
    # stdlib module records the comparisons the request actually performs.
    monkeypatch.setattr(secrets, "compare_digest", recording_compare_digest)

    async with _app_clients(tmp_path, [TOKEN_ALPHA, TOKEN_BETA]) as (alice, _, _):
        response = await alice.get("/api/v1/validations", headers=_bearer(TOKEN_BETA))
        assert response.status_code == 200

    # Every configured token is compared, even after a match, so response
    # timing does not reveal which token position matched.
    supplied = TOKEN_BETA.encode("utf-8")
    assert (supplied, TOKEN_ALPHA.encode("utf-8")) in calls
    assert (supplied, TOKEN_BETA.encode("utf-8")) in calls


async def test_auth_off_ignores_authorization_headers(
    client: AsyncClient, clean_csv: bytes
) -> None:
    """With no configured tokens, requests keep today's cookie scoping."""
    created = await client.post(
        "/api/v1/validations",
        files=_files(clean_csv),
        headers=_bearer("some-random-bearer-token"),
    )
    assert created.status_code == 201
    assert "eav_session" in created.cookies

    history = await client.get("/api/v1/validations")
    assert [item["id"] for item in history.json()] == [created.json()["id"]]


async def test_cookie_in_the_token_namespace_is_replaced(
    client: AsyncClient, clean_csv: bytes
) -> None:
    """A crafted cookie cannot collide with hashed-token scope keys."""
    forged = "token:" + hashlib.sha256(b"guessed").hexdigest()
    client.cookies.set("eav_session", forged)

    created = await client.post("/api/v1/validations", files=_files(clean_csv))
    assert created.status_code == 201
    assert created.cookies.get("eav_session") not in (None, forged)
