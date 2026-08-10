from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

from electrical_asset_validator.services.comparison import compare_datasets
from electrical_asset_validator.services.ingest import (
    DatasetError,
    parse_column_mapping,
    parse_dataset,
)
from electrical_asset_validator.services.validation import validate_dataset

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CASE_STUDY_DATA = PROJECT_ROOT / "sample-data" / "case-study"

# The same mapping the walkthrough passes in the `mapping` form field.
CASE_STUDY_MAPPING = json.dumps(
    {
        "Tag": "asset_tag",
        "Panel": "panel_tag",
        "Voltage (V)": "voltage_v",
        "Power (kW)": "power_kw",
    }
)


def _case_study(name: str):
    path = CASE_STUDY_DATA / name
    mapping = parse_column_mapping(CASE_STUDY_MAPPING)
    return parse_dataset(path.name, path.read_bytes(), mapping)


def test_case_study_walkthrough_remains_reproducible() -> None:
    """Pin docs/case-study.md to the output the rules actually produce."""
    as_received = _case_study("register-as-received.csv")
    corrected = _case_study("register-corrected.csv")

    received_validation = validate_dataset(as_received)
    corrected_validation = validate_dataset(corrected)

    assert received_validation.quality_score == 72.7
    assert received_validation.total_rows == 22
    assert received_validation.valid_rows == 16
    assert received_validation.error_count == 6
    assert received_validation.warning_count == 4
    assert received_validation.info_count == 0
    assert Counter(
        (finding.severity, finding.rule) for finding in received_validation.findings
    ) == Counter(
        {
            ("error", "DUPLICATE_ASSET_TAG"): 2,
            ("error", "REQUIRED_FIELD"): 2,
            ("error", "VALUE_OUT_OF_RANGE"): 1,
            ("error", "INVALID_STATUS"): 1,
            ("warning", "NAMING_NORMALIZATION"): 1,
            ("warning", "UNKNOWN_PANEL_REFERENCE"): 1,
            ("warning", "MISSING_PANEL_REFERENCE"): 1,
            ("warning", "MISSING_CIRCUIT_REFERENCE"): 1,
        }
    )
    status_finding = next(
        finding
        for finding in received_validation.findings
        if finding.rule == "NAMING_NORMALIZATION"
    )
    assert status_finding.suggestion == "active"

    assert corrected_validation.quality_score == 100
    assert corrected_validation.findings == []
    assert corrected_validation.total_rows == 24
    assert corrected_validation.valid_rows == 24

    # The documented refusal: a duplicate tag blocks the revision diff.
    with pytest.raises(DatasetError, match="duplicate asset_tag 'FAN-C-02'"):
        compare_datasets(as_received, corrected)
