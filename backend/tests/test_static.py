from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from electrical_asset_validator.config import Settings
from electrical_asset_validator.main import create_app


def _settings(tmp_path: Path, **overrides: Any) -> Settings:
    database_path = (tmp_path / "static-test.db").as_posix()
    return Settings(
        database_url=f"sqlite:///{database_path}",
        docs_enabled=False,
        max_upload_mb=1,
        **overrides,
    )


@pytest.mark.anyio
async def test_static_dir_serves_frontend_and_keeps_api(tmp_path: Path) -> None:
    static_root = tmp_path / "dist"
    static_root.mkdir()
    (static_root / "index.html").write_text("<html><body>frontend</body></html>")

    application = create_app(_settings(tmp_path, static_dir=str(static_root)))
    transport = ASGITransport(app=application)
    async with application.router.lifespan_context(application):
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            index = await client.get("/")
            assert index.status_code == 200
            assert "frontend" in index.text

            health = await client.get("/api/v1/health")
            assert health.status_code == 200


@pytest.mark.anyio
async def test_root_is_not_served_without_static_dir(tmp_path: Path) -> None:
    application = create_app(_settings(tmp_path))
    transport = ASGITransport(app=application)
    async with application.router.lifespan_context(application):
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            assert (await client.get("/")).status_code == 404


def test_missing_static_dir_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="EAV_STATIC_DIR"):
        create_app(_settings(tmp_path, static_dir=str(tmp_path / "absent")))
