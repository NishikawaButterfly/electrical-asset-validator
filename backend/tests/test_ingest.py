from __future__ import annotations

from io import BytesIO

import pytest
from openpyxl import Workbook

from electrical_asset_validator.services import ingest
from electrical_asset_validator.services.ingest import (
    CANONICAL_COLUMNS,
    DatasetError,
    parse_dataset,
)


def test_csv_headers_are_safely_normalized() -> None:
    content = (
        "Asset Tag,Asset Name,Asset Type,Location,Panel Tag,Circuit Ref,"
        "Voltage V,Power KW,Status\n"
        "PNL-A,Main Panel,panel,Plant 1,,,400,0,active\n"
    ).encode()

    dataset = parse_dataset("assets.csv", content)

    assert dataset.present_columns == set(CANONICAL_COLUMNS)
    assert dataset.records[0]["asset_tag"] == "PNL-A"
    assert dataset.records[0]["panel_tag"] is None
    assert dataset.records[0]["voltage_v"] == 400
    assert dataset.records[0]["power_kw"] == 0


def test_xlsx_first_worksheet_is_supported() -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(CANONICAL_COLUMNS)
    sheet.append(
        ["PNL-A", "Main Panel", "panel", "Plant 1", None, None, 400, 0, "active"]
    )
    output = BytesIO()
    workbook.save(output)

    dataset = parse_dataset("assets.xlsx", output.getvalue())

    assert len(dataset.records) == 1
    assert dataset.records[0]["voltage_v"] == 400


def test_blank_csv_lines_do_not_shift_source_row_numbers() -> None:
    content = (
        ",".join(CANONICAL_COLUMNS)
        + "\n"
        + "PNL-A,Main Panel,panel,Plant 1,,,400,0,active\n"
        + "\n"
        + "MTR-001,Motor,motor,Plant 1,PNL-A,C-01,400,-1,active\n"
    ).encode()

    dataset = parse_dataset("assets.csv", content)

    assert dataset.row_numbers == [2, 4]
    assert dataset.records[1]["power_kw"] == -1


def test_literal_na_text_is_not_coerced_to_missing() -> None:
    content = (
        ",".join(CANONICAL_COLUMNS)
        + "\n"
        + "PNL-A,NA,panel,N/A,,,400,0,active\n"
    ).encode()

    dataset = parse_dataset("assets.csv", content)

    assert dataset.records[0]["asset_name"] == "NA"
    assert dataset.records[0]["location"] == "N/A"


def test_exact_duplicate_xlsx_headers_are_rejected() -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["asset_tag", "asset_tag"])
    sheet.append(["PNL-A", "PNL-B"])
    output = BytesIO()
    workbook.save(output)

    with pytest.raises(DatasetError, match="Duplicate columns"):
        parse_dataset("assets.xlsx", output.getvalue())


def test_row_limit_is_enforced_before_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(ingest, "MAX_ROWS", 1)
    content = (
        ",".join(CANONICAL_COLUMNS)
        + "\n"
        + "PNL-A,Panel A,panel,Plant 1,,,400,0,active\n"
        + "PNL-B,Panel B,panel,Plant 1,,,400,0,active\n"
    ).encode()

    with pytest.raises(DatasetError, match="no more than 1 data rows"):
        parse_dataset("assets.csv", content)


def test_xlsx_row_limit_counts_non_empty_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(ingest, "MAX_ROWS", 1)
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(CANONICAL_COLUMNS)
    sheet.append([None] * len(CANONICAL_COLUMNS))
    sheet.append(
        ["PNL-A", "Main Panel", "panel", "Plant 1", None, None, 400, 0, "active"]
    )
    output = BytesIO()
    workbook.save(output)

    dataset = parse_dataset("sparse.xlsx", output.getvalue())

    assert dataset.row_numbers == [3]
    assert len(dataset.records) == 1


@pytest.mark.parametrize(
    ("filename", "content", "message"),
    [
        ("assets.txt", b"anything", "Only .csv and .xlsx"),
        ("assets.csv", b"", "empty"),
        ("assets.csv", b"asset_tag\n", "data rows"),
        (
            "assets.csv",
            b"Asset Tag,asset_tag\nA,B\n",
            "Duplicate columns",
        ),
        (
            "assets.csv",
            b"asset_tag,asset_tag\nA,B\n",
            "Duplicate columns",
        ),
    ],
)
def test_malformed_datasets_are_rejected(
    filename: str, content: bytes, message: str
) -> None:
    with pytest.raises(DatasetError, match=message):
        parse_dataset(filename, content)
