from __future__ import annotations

from io import BytesIO

import pytest
from openpyxl import Workbook

from tests.conftest import csv_bytes

from electrical_asset_validator.services import comparison as comparison_service
from electrical_asset_validator.services.comparison import compare_datasets
from electrical_asset_validator.services.ingest import (
    CANONICAL_COLUMNS,
    DatasetError,
    parse_dataset,
)


def _row(tag: str, name: str, power: int) -> dict[str, object]:
    return {
        "asset_tag": tag,
        "asset_name": name,
        "asset_type": "motor",
        "location": "Plant 1",
        "panel_tag": "PNL-A",
        "circuit_ref": f"C-{tag[-1]}",
        "voltage_v": 400,
        "power_kw": power,
        "status": "active",
    }


def test_compare_by_asset_tag_reports_all_change_types() -> None:
    before = parse_dataset(
        "before.csv",
        csv_bytes(
            [
                _row("MTR-001", "Motor 1", 10),
                _row("MTR-002", "Motor 2", 20),
                _row("MTR-003", "Motor 3", 30),
            ]
        ),
    )
    after = parse_dataset(
        "after.csv",
        csv_bytes(
            [
                _row("MTR-001", "Motor 1", 10),
                _row("MTR-002", "Motor 2", 25),
                _row("MTR-004", "Motor 4", 40),
            ]
        ),
    )

    outcome = compare_datasets(before, after)

    assert outcome.added == [{"asset_tag": "MTR-004", "row": 4}]
    assert outcome.removed == [{"asset_tag": "MTR-003", "row": 4}]
    assert outcome.unchanged == 1
    assert outcome.changed == [
        {
            "asset_tag": "MTR-002",
            "changes": [{"field": "power_kw", "before": 20, "after": 25}],
        }
    ]


def test_comparison_rejects_ambiguous_tags() -> None:
    before = parse_dataset(
        "before.csv",
        csv_bytes(
            [
                _row("MTR-001", "Motor 1", 10),
                _row("mtr_001", "Motor duplicate", 20),
            ]
        ),
    )
    after = parse_dataset("after.csv", csv_bytes([_row("MTR-001", "Motor", 10)]))

    with pytest.raises(DatasetError, match="duplicate asset_tag"):
        compare_datasets(before, after)


def test_comparison_requires_the_complete_canonical_schema() -> None:
    incomplete = parse_dataset(
        "before.csv",
        b"asset_tag,asset_name\nMTR-001,Motor\n",
    )
    complete = parse_dataset(
        "after.csv",
        csv_bytes([_row("MTR-001", "Motor", 10)]),
    )

    with pytest.raises(DatasetError, match="missing canonical columns"):
        compare_datasets(incomplete, complete)


def test_comparison_rejects_a_unique_noncanonical_tag() -> None:
    before = parse_dataset(
        "before.csv",
        csv_bytes([_row("mtr_001", "Motor", 10)]),
    )
    after = parse_dataset(
        "after.csv",
        csv_bytes([_row("MTR-001", "Motor", 10)]),
    )

    with pytest.raises(DatasetError, match="invalid asset_tag"):
        compare_datasets(before, after)


def test_equivalent_csv_and_xlsx_numbers_compare_as_unchanged() -> None:
    row = _row("MTR-001", "Motor", 10)
    before = parse_dataset("before.csv", csv_bytes([row]))

    workbook = Workbook()
    sheet = workbook.active
    sheet.append(CANONICAL_COLUMNS)
    sheet.append([row[column] for column in CANONICAL_COLUMNS])
    output = BytesIO()
    workbook.save(output)
    after = parse_dataset("after.xlsx", output.getvalue())

    outcome = compare_datasets(before, after)

    assert outcome.unchanged == 1
    assert outcome.added == []
    assert outcome.removed == []
    assert outcome.changed == []


def test_equivalent_textual_csv_and_numeric_xlsx_cells_are_unchanged() -> None:
    csv_row = _row("MTR-001", "123", 10)
    csv_row["location"] = "1"
    before = parse_dataset("before.csv", csv_bytes([csv_row]))

    xlsx_row = dict(csv_row)
    xlsx_row["asset_name"] = 123
    xlsx_row["location"] = 1
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(CANONICAL_COLUMNS)
    sheet.append([xlsx_row[column] for column in CANONICAL_COLUMNS])
    output = BytesIO()
    workbook.save(output)
    after = parse_dataset("after.xlsx", output.getvalue())

    outcome = compare_datasets(before, after)

    assert outcome.unchanged == 1
    assert outcome.changed == []


def test_comparison_detail_output_is_bounded(monkeypatch) -> None:
    monkeypatch.setattr(comparison_service, "MAX_COMPARISON_DETAILS", 1)
    before = parse_dataset(
        "before.csv",
        csv_bytes([_row("MTR-001", "Motor 1", 10)]),
    )
    after = parse_dataset(
        "after.csv",
        csv_bytes([_row("MTR-001", "Renamed Motor", 20)]),
    )

    with pytest.raises(DatasetError, match="1-detail output limit"):
        compare_datasets(before, after)
