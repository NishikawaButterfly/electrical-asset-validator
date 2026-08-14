from __future__ import annotations

import csv
import re
from collections.abc import AsyncIterator
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile

import pytest
from httpx import ASGITransport, AsyncClient
from openpyxl import Workbook

from electrical_asset_validator.config import Settings
from electrical_asset_validator.main import create_app
from electrical_asset_validator.services.ingest import CANONICAL_COLUMNS

# A register built the way engineers build one: the ratings are derived rather
# than typed. Sheet row 2 is the panel and row 3 the motor; column G holds
# voltage_v and column H holds power_kw.
FORMULA_ROWS: list[list[Any]] = [
    ["PNL-A", "Main Panel", "panel", "Plant 1", None, None, "=200*2", 0, "active"],
    ["MTR-001", "Motor", "motor", "Plant 1", "PNL-A", "C-01", "=200*2", "=7.5*2", "active"],
]
# What a spreadsheet application would have stored for each of those formulas.
FORMULA_RESULTS = {"G2": "400", "G3": "400", "H3": "15"}


def csv_bytes(rows: list[dict[str, Any]]) -> bytes:
    output = StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=CANONICAL_COLUMNS)
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def xlsx_bytes(rows: list[list[Any]], header: list[Any] | None = None) -> bytes:
    """Write a workbook the way a script writes one.

    A string beginning with ``=`` becomes a real formula, and openpyxl never
    calculates it, so the workbook carries no result for it. That is exactly
    what a register exported by openpyxl or pandas looks like.
    """
    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.append(list(CANONICAL_COLUMNS) if header is None else header)
    for row in rows:
        sheet.append(row)
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def with_cached_values(content: bytes, cached: dict[str, str]) -> bytes:
    """Store the results a spreadsheet application would have cached.

    openpyxl writes a formula cell as ``<c r="G3"><f>200*2</f><v /></c>`` --
    the formula with an empty result element. Excel and LibreOffice fill that
    element in every time they save. Neither is available here or in CI, so the
    tests write the result into the sheet XML themselves, which produces a file
    byte-for-byte equivalent to one a spreadsheet application had saved.
    """
    with ZipFile(BytesIO(content)) as archive:
        names = archive.namelist()
        entries = {name: archive.read(name) for name in names}

    sheet_xml = entries["xl/worksheets/sheet1.xml"].decode("utf-8")
    for reference, value in cached.items():
        # A cached result that is a spreadsheet error carries t="e"; anything
        # else is a plain number, which is the default and needs no attribute.
        cell_type = ' t="e"' if value.startswith("#") else ""
        pattern = re.compile(rf'<c r="{reference}"([^>]*)>(\s*<f>.*?</f>\s*)<v\s*/>')
        sheet_xml, replaced = pattern.subn(
            rf'<c r="{reference}"\g<1>{cell_type}>\g<2><v>{value}</v>', sheet_xml
        )
        assert replaced == 1, f"{reference} does not hold an uncalculated formula"
    entries["xl/worksheets/sheet1.xml"] = sheet_xml.encode("utf-8")

    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for name in names:
            archive.writestr(name, entries[name])
    return output.getvalue()


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
