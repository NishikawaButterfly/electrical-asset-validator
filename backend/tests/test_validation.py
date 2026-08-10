from __future__ import annotations

from electrical_asset_validator.services import validation as validation_service
from electrical_asset_validator.services.ingest import CANONICAL_COLUMNS, parse_dataset
from electrical_asset_validator.services.validation import (
    MAX_ASSET_TAG_CHARACTERS,
    validate_dataset,
)
from tests.conftest import csv_bytes


def test_clean_register_scores_100(clean_rows: list[dict[str, object]]) -> None:
    dataset = parse_dataset("clean.csv", csv_bytes(clean_rows))

    outcome = validate_dataset(dataset)

    assert outcome.quality_score == 100
    assert outcome.valid_rows == 2
    assert outcome.findings == []


def test_core_data_quality_rules_are_reported(
    clean_rows: list[dict[str, object]],
) -> None:
    rows = [
        *clean_rows,
        {
            "asset_tag": "mtr_001",
            "asset_name": "Backup Motor",
            "asset_type": "motor",
            "location": "Plant 1",
            "panel_tag": "PNL-X",
            "circuit_ref": "c 1",
            "voltage_v": -10,
            "power_kw": "large",
            "status": "activ",
        },
    ]
    dataset = parse_dataset("bad.csv", csv_bytes(rows))

    outcome = validate_dataset(dataset)
    rules = {finding.rule for finding in outcome.findings}

    assert {
        "ASSET_TAG_FORMAT",
        "DUPLICATE_ASSET_TAG",
        "INVALID_NUMBER",
        "VALUE_OUT_OF_RANGE",
        "INVALID_STATUS",
        "UNKNOWN_PANEL_REFERENCE",
        "CIRCUIT_REFERENCE_FORMAT",
    } <= rules
    assert outcome.valid_rows == 1
    assert outcome.quality_score < 100
    assert all(finding.severity in {"error", "warning", "info"} for finding in outcome.findings)
    status_finding = next(
        finding for finding in outcome.findings if finding.rule == "INVALID_STATUS"
    )
    assert status_finding.suggestion == "active"


def test_missing_schema_and_reference_fields_are_distinguished() -> None:
    content = (
        b"asset_tag,asset_name,asset_type,location,voltage_v,power_kw,status\n"
        b"MTR-001,Motor,motor,Plant 1,400,10,active\n"
    )

    outcome = validate_dataset(parse_dataset("missing.csv", content))
    rules_by_field = {(finding.rule, finding.field) for finding in outcome.findings}

    assert ("MISSING_COLUMN", "panel_tag") in rules_by_field
    assert ("MISSING_COLUMN", "circuit_ref") in rules_by_field
    assert ("MISSING_PANEL_REFERENCE", "panel_tag") in rules_by_field
    assert ("MISSING_CIRCUIT_REFERENCE", "circuit_ref") in rules_by_field
    assert outcome.valid_rows == 0
    assert outcome.quality_score == 0


def test_inconsistent_panel_metadata_is_reported() -> None:
    rows = [
        {
            "asset_tag": "PNL-A",
            "asset_name": "Panel",
            "asset_type": "motor",
            "location": "Room A",
            "panel_tag": "",
            "circuit_ref": "",
            "voltage_v": 400,
            "power_kw": 1,
            "status": "decommissioned",
        },
        {
            "asset_tag": "MTR-001",
            "asset_name": "Motor",
            "asset_type": "motor",
            "location": "Room B",
            "panel_tag": "PNL-A",
            "circuit_ref": "C-01",
            "voltage_v": 400,
            "power_kw": 10,
            "status": "active",
        },
    ]

    outcome = validate_dataset(parse_dataset("references.csv", csv_bytes(rows)))
    rules = {finding.rule for finding in outcome.findings}

    assert "INVALID_PANEL_REFERENCE" in rules
    assert "PANEL_LOCATION_MISMATCH" in rules


def test_information_findings_do_not_reduce_quality_score() -> None:
    content = (
        ",".join([*CANONICAL_COLUMNS, "review_note"])
        + "\n"
        + "PNL-A,Panel A,panel,Plant 1,,,400,0,active,fictional\n"
    ).encode()

    outcome = validate_dataset(parse_dataset("extra.csv", content))

    assert outcome.info_count == 1
    assert outcome.error_count == 0
    assert outcome.warning_count == 0
    assert outcome.quality_score == 100


def test_blank_lines_preserve_finding_source_rows() -> None:
    content = (
        ",".join(CANONICAL_COLUMNS)
        + "\n"
        + "PNL-A,Panel A,panel,Plant 1,,,400,0,active\n"
        + "\n"
        + "MTR-001,Motor,motor,Plant 1,PNL-A,C-01,400,-1,active\n"
    ).encode()

    outcome = validate_dataset(parse_dataset("rows.csv", content))
    power_finding = next(
        finding
        for finding in outcome.findings
        if finding.rule == "VALUE_OUT_OF_RANGE" and finding.field == "power_kw"
    )

    assert power_finding.row == 4


def test_overlong_asset_tags_are_blocking_errors() -> None:
    tag = "A" * (MAX_ASSET_TAG_CHARACTERS + 1)
    content = (
        ",".join(CANONICAL_COLUMNS) + "\n" + f"{tag},Panel A,panel,Plant 1,,,400,0,active\n"
    ).encode()

    outcome = validate_dataset(parse_dataset("long-tag.csv", content))

    assert any(finding.rule == "ASSET_TAG_LENGTH" for finding in outcome.findings)
    assert outcome.valid_rows == 0


def test_score_cannot_round_to_100_when_a_blocking_error_exists() -> None:
    rows = [
        {
            "asset_tag": f"PNL-{index:04d}",
            "asset_name": "" if index == 0 else f"Panel {index}",
            "asset_type": "panel",
            "location": "Plant 1",
            "panel_tag": "",
            "circuit_ref": "",
            "voltage_v": 400,
            "power_kw": 0,
            "status": "active",
        }
        for index in range(2_000)
    ]

    outcome = validate_dataset(parse_dataset("large.csv", csv_bytes(rows)))

    assert outcome.error_count == 1
    assert outcome.valid_rows == 1_999
    assert outcome.quality_score == 99.9


def test_finding_output_is_bounded(
    monkeypatch,
    clean_rows: list[dict[str, object]],
) -> None:
    monkeypatch.setattr(validation_service, "MAX_FINDINGS", 5)
    invalid_rows = [dict(row) for row in clean_rows]
    for row in invalid_rows:
        row.update(
            {
                "asset_name": "",
                "asset_type": "",
                "location": "",
                "panel_tag": "",
                "circuit_ref": "",
                "voltage_v": -1,
                "power_kw": "not-a-number",
                "status": "unknown",
            }
        )

    outcome = validate_dataset(parse_dataset("many-findings.csv", csv_bytes(invalid_rows)))

    assert len(outcome.findings) == 5
    assert outcome.findings[-1].rule == "FINDING_LIMIT_REACHED"
    assert outcome.valid_rows == 0
    assert outcome.error_count > 4
    assert outcome.issue_count > len(outcome.findings)
    assert outcome.returned_issue_count == 5
    assert outcome.issues_truncated is True
