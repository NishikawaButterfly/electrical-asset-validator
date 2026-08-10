from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import timedelta
from pathlib import Path
from typing import Any

from httpx import ASGITransport, AsyncClient
import pytest

from electrical_asset_validator.config import Settings
from electrical_asset_validator.main import create_app
from electrical_asset_validator.models import utc_now

pytestmark = pytest.mark.anyio


def _files(content: bytes, filename: str = "assets.csv") -> dict[str, Any]:
    return {"file": (filename, content, "text/csv")}


@asynccontextmanager
async def _two_clients(
    tmp_path: Path, **overrides: Any
) -> AsyncIterator[tuple[AsyncClient, AsyncClient]]:
    """One application, two browser sessions with independent cookie jars."""
    database_path = (tmp_path / "privacy.db").as_posix()
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        docs_enabled=False,
        max_upload_mb=1,
        **overrides,
    )
    application = create_app(settings)
    transport = ASGITransport(app=application)
    async with application.router.lifespan_context(application):
        async with (
            AsyncClient(transport=transport, base_url="http://testserver") as first,
            AsyncClient(transport=transport, base_url="http://testserver") as second,
        ):
            yield first, second


async def test_listing_is_scoped_to_the_creating_session(tmp_path: Path, clean_csv: bytes) -> None:
    async with _two_clients(tmp_path) as (alice, bob):
        created = await alice.post("/api/v1/validations", files=_files(clean_csv))
        assert created.status_code == 201
        assert "eav_session" in created.cookies

        own_history = await alice.get("/api/v1/validations")
        assert own_history.status_code == 200
        assert [item["id"] for item in own_history.json()] == [created.json()["id"]]

        other_history = await bob.get("/api/v1/validations")
        assert other_history.status_code == 200
        assert other_history.json() == []


async def test_foreign_validation_and_reports_return_404(tmp_path: Path, clean_csv: bytes) -> None:
    async with _two_clients(tmp_path) as (alice, bob):
        created = await alice.post("/api/v1/validations", files=_files(clean_csv))
        assert created.status_code == 201
        validation_id = created.json()["id"]

        own = await alice.get(f"/api/v1/validations/{validation_id}")
        assert own.status_code == 200

        for path in (
            f"/api/v1/validations/{validation_id}",
            f"/api/v1/validations/{validation_id}/report.xlsx",
            f"/api/v1/validations/{validation_id}/report.pdf",
        ):
            foreign = await bob.get(path)
            assert foreign.status_code == 404


async def test_foreign_comparison_returns_404(tmp_path: Path, clean_csv: bytes) -> None:
    async with _two_clients(tmp_path) as (alice, bob):
        created = await alice.post(
            "/api/v1/comparisons",
            files={
                "before_file": ("before.csv", clean_csv, "text/csv"),
                "after_file": ("after.csv", clean_csv, "text/csv"),
            },
        )
        assert created.status_code == 201
        comparison_id = created.json()["id"]

        own = await alice.get(f"/api/v1/comparisons/{comparison_id}")
        assert own.status_code == 200

        foreign = await bob.get(f"/api/v1/comparisons/{comparison_id}")
        assert foreign.status_code == 404


async def test_session_cookie_is_httponly(tmp_path: Path, clean_csv: bytes) -> None:
    async with _two_clients(tmp_path) as (alice, _):
        created = await alice.post("/api/v1/validations", files=_files(clean_csv))
        assert created.status_code == 201
        set_cookie = created.headers["set-cookie"].lower()
        assert "httponly" in set_cookie
        assert "samesite=lax" in set_cookie


async def test_validation_ids_are_not_sequential(tmp_path: Path, clean_csv: bytes) -> None:
    async with _two_clients(tmp_path) as (alice, _):
        first = await alice.post("/api/v1/validations", files=_files(clean_csv))
        second = await alice.post("/api/v1/validations", files=_files(clean_csv))
        first_id = first.json()["id"]
        second_id = second.json()["id"]

        assert not first_id.isdigit()
        assert not second_id.isdigit()
        # Both parse as UUIDs, so consecutive creations cannot differ by one.
        assert uuid.UUID(first_id) != uuid.UUID(second_id)


async def test_retention_sweep_deletes_expired_runs(
    tmp_path: Path,
    clean_csv: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from electrical_asset_validator import retention

    async with _two_clients(tmp_path, demo_retention_minutes=30) as (alice, _):
        validation = await alice.post("/api/v1/validations", files=_files(clean_csv))
        comparison = await alice.post(
            "/api/v1/comparisons",
            files={
                "before_file": ("before.csv", clean_csv, "text/csv"),
                "after_file": ("after.csv", clean_csv, "text/csv"),
            },
        )
        assert validation.status_code == 201
        assert comparison.status_code == 201
        validation_id = validation.json()["id"]
        comparison_id = comparison.json()["id"]

        # Still inside the retention window.
        assert (await alice.get(f"/api/v1/validations/{validation_id}")).status_code == 200

        future = utc_now() + timedelta(minutes=31)
        monkeypatch.setattr(retention, "utc_now", lambda: future)

        history = await alice.get("/api/v1/validations")
        assert history.status_code == 200
        assert history.json() == []
        assert (await alice.get(f"/api/v1/validations/{validation_id}")).status_code == 404
        assert (await alice.get(f"/api/v1/comparisons/{comparison_id}")).status_code == 404


async def test_retention_disabled_by_default(
    tmp_path: Path,
    clean_csv: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from electrical_asset_validator import retention

    async with _two_clients(tmp_path) as (alice, _):
        created = await alice.post("/api/v1/validations", files=_files(clean_csv))
        assert created.status_code == 201

        future = utc_now() + timedelta(days=365)
        monkeypatch.setattr(retention, "utc_now", lambda: future)

        history = await alice.get("/api/v1/validations")
        assert len(history.json()) == 1
