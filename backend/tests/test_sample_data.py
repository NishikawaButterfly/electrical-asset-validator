from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path
from typing import Any

import pytest

from electrical_asset_validator.services.comparison import compare_datasets
from electrical_asset_validator.services.ingest import Dataset, parse_dataset
from electrical_asset_validator.services.validation import validate_dataset
from tests.conftest import xlsx_bytes

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_DATA = PROJECT_ROOT / "sample-data"


def _sample(name: str) -> Dataset:
    path = SAMPLE_DATA / name
    return parse_dataset(path.name, path.read_bytes())


def test_documented_sample_workflows_remain_reproducible() -> None:
    revision_a = _sample("revision-a.csv")
    revision_b = _sample("revision-b.csv")
    invalid_register = _sample("invalid-register.csv")

    baseline_validation = validate_dataset(revision_a)
    candidate_validation = validate_dataset(revision_b)
    invalid_validation = validate_dataset(invalid_register)
    comparison = compare_datasets(revision_a, revision_b)

    assert baseline_validation.quality_score == 100
    assert baseline_validation.findings == []
    assert candidate_validation.quality_score == 100
    assert candidate_validation.findings == []
    assert invalid_validation.error_count == 7
    assert invalid_validation.warning_count == 5
    assert invalid_validation.quality_score == 58.2
    commissioning_finding = next(
        finding for finding in invalid_validation.findings if finding.rule == "INVALID_STATUS"
    )
    assert commissioning_finding.suggestion is None
    assert len(comparison.added) == 1
    assert len(comparison.removed) == 1
    assert len(comparison.changed) == 4
    assert comparison.unchanged == 10


@pytest.mark.parametrize("name", ["revision-a.csv", "invalid-register.csv"])
def test_a_workbook_without_formulas_reads_exactly_as_its_csv(name: str) -> None:
    """A register that holds no formula must be untouched by the formula path."""
    path = SAMPLE_DATA / name
    reader = csv.reader(StringIO(path.read_text(encoding="utf-8"), newline=""))
    header = next(reader)
    rows: list[list[Any]] = [[cell or None for cell in row] for row in reader]

    from_csv = validate_dataset(parse_dataset(path.name, path.read_bytes()))
    from_xlsx = validate_dataset(
        parse_dataset(f"{path.stem}.xlsx", xlsx_bytes(rows, header=header))
    )

    assert from_xlsx.quality_score == from_csv.quality_score
    assert from_xlsx.findings == from_csv.findings
    assert from_xlsx.records == from_csv.records
