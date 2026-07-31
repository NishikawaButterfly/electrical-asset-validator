from __future__ import annotations

import csv
from collections.abc import AsyncIterator
from io import StringIO
from pathlib import Path
from typing import Any

from httpx import ASGITransport, AsyncClient
import pytest

from electrical_asset_validator.config import Settings
from electrical_asset_validator.main import create_app
from electrical_asset_validator.services.ingest import CANONICAL_COLUMNS


def csv_bytes(rows: list[dict[str, Any]]) -> bytes:
    output = StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=CANONICAL_COLUMNS)
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


@pytest.fixture
def clean_rows() -> list[dict[str, Any]]:
    return [
        {
            "asset_tag": "PNL-A",
            "asset_name": "Main Panel",
            "asset_type": "panel",
            "location": "Plant 1",
            "panel_tag": "",
            "circuit_ref": "",
            "voltage_v": 400,
            "power_kw": 0,
            "status": "active",
        },
        {
            "asset_tag": "MTR-001",
            "asset_name": "Conveyor Motor",
            "asset_type": "motor",
            "location": "Plant 1",
            "panel_tag": "PNL-A",
            "circuit_ref": "C-01",
            "voltage_v": 400,
            "power_kw": 15,
            "status": "active",
        },
    ]


@pytest.fixture
def clean_csv(clean_rows: list[dict[str, Any]]) -> bytes:
    return csv_bytes(clean_rows)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def client(tmp_path: Path) -> AsyncIterator[AsyncClient]:
    database_path = (tmp_path / "test.db").as_posix()
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        docs_enabled=False,
        max_upload_mb=1,
    )
    application = create_app(settings)
    transport = ASGITransport(app=application)
    async with application.router.lifespan_context(application):
        async with AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as test_client:
            yield test_client
